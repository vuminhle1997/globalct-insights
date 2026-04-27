import asyncio
import json
import os
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

from chromadb import Collection
from fastapi import BackgroundTasks, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_pagination
from llama_index.core import PromptTemplate
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.llms import ChatMessage as LLMChatMessage, MessageRole
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.settings import Settings
from llama_index.core.tools import BaseTool
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
from redis import Redis
from starlette.requests import Request

from backend.dependencies import (
    SessionDep,
    base_url,
    get_chroma_collection,
    get_chroma_vector,
    get_redis_client,
    logger,
)
from backend.models.chat import Chat, ChatPublic, ChatQuery
from backend.models.chat_file import ChatFile
from backend.models.chat_message import ChatMessage
from backend.routers.custom_router import APIRouter
from backend.services.indexer import deletes_file_index_from_collection, index_spreadsheet, index_uploaded_file
from backend.services.llm_agent import create_agent
from backend.services.memory import create_memory
from backend.services.tasks import process_dump_to_persist
from backend.services.tools_initializer import (
    create_pandas_engines_tools_from_files,
    create_query_engine_tools,
    create_search_engine_tool,
    create_sql_engines_tools_from_files,
    create_url_loader_tool,
)
from backend.utils.check_property import check_property_belongs_to_user
from backend.utils.jwt import decode_jwt
from backend.utils.upload_sql_dump import delete_database_from_postgres, detect_sql_dump_type

BASE_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    prefix="/chats",
    tags=["chats"],
    responses={404: {"description": "Not found"}},
)


def serialize_chat_file(chat_file: ChatFile) -> dict:
    return {
        "id": chat_file.id,
        "file_name": chat_file.file_name,
        "path_name": chat_file.path_name,
        "mime_type": chat_file.mime_type,
        "indexed": chat_file.indexed,
        "chat_id": chat_file.chat_id,
        "database_name": chat_file.database_name,
        "database_type": chat_file.database_type,
        "tables": chat_file.tables,
        "created_at": chat_file.created_at,
        "updated_at": chat_file.updated_at,
    }


def serialize_chat_message(chat_message: ChatMessage) -> dict:
    return {
        "id": chat_message.id,
        "role": chat_message.role,
        "additional_kwargs": chat_message.additional_kwargs,
        "block_type": chat_message.block_type,
        "text": chat_message.text,
        "created_at": chat_message.created_at,
        "chat_id": chat_message.chat_id,
    }


def serialize_favourite(favourite) -> dict | None:
    if favourite is None:
        return None

    return {
        "id": favourite.id,
        "created_at": favourite.created_at,
        "chat_id": favourite.chat_id,
        "user_id": favourite.user_id,
    }


def serialize_chat(chat: Chat, *, include_files: bool = False) -> dict:
    serialized_chat = {
        "id": chat.id,
        "title": chat.title,
        "description": chat.description,
        "context": chat.context,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "last_interacted_at": chat.last_interacted_at,
        "user_id": chat.user_id,
        "avatar_path": chat.avatar_path,
        "temperature": chat.temperature,
        "model": chat.model,
    }
    if include_files:
        serialized_chat["files"] = [serialize_chat_file(chat_file) for chat_file in chat.files]
    return serialized_chat


def initialize_ionos_llm(temperature: float):
    """
    Initializes and returns an instance of an OpenAI-compatible LLM (OpenAILike) configured for IONOS deployment.

    This function loads environment variables (e.g., `IONOS_BASE_URL`, `IONOS_API_KEY`) from a `.env` file
    and uses them to configure the connection to a local or remote IONOS-compatible LLM API.

    Parameters:
    -----------
    temperature : float
        The temperature parameter for the LLM, controlling the randomness of the output.
        Higher values (e.g., 1.0) yield more diverse output, while lower values (e.g., 0.2) make it more deterministic.

    Returns:
    --------
    OpenAILike
        An instance of the `OpenAILike` LLM from LlamaIndex, configured to use the IONOS endpoint with provided settings.

    Environment Variables:
    ----------------------
    - IONOS_BASE_URL : str
        The base URL of the IONOS-compatible LLM API (e.g., http://localhost:11434).
    - IONOS_API_KEY : str
        The API key used for authenticating with the IONOS LLM endpoint.

    Notes:
    ------
    - Defaults are used if environment variables are not set.
    - The `OPENAI_API_BASE` and `OPENAI_API_KEY` are set globally in the environment to ensure
      compatibility with tools expecting OpenAI-like APIs.
    """
    import os

    from dotenv import load_dotenv
    from llama_index.llms.openai_like import OpenAILike

    load_dotenv()  # Load environment variables from .env file

    # Read base URL and API key from environment variables or fallback to defaults
    base_url = os.getenv("IONOS_BASE_URL", "http://localhost:11434")
    api_key = os.getenv("IONOS_API_KEY", "your_api_key_here")

    # Set required environment variables for OpenAI-compatible API access
    os.environ["OPENAI_API_BASE"] = base_url
    os.environ["OPENAI_API_KEY"] = api_key

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Instantiate the OpenAILike LLM with specified parameters
    llm = OpenAILike(
        api_base=base_url,
        temperature=temperature,
        model="meta-llama/Llama-3.3-70B-Instruct",
        is_chat_model=True,
        default_headers=headers,
        api_key=api_key,
        context_window=128000,
    )

    return llm


async def stream_agent_response(
    agent: ReActAgent,
    user_input: str,
    db_client: SessionDep,
    chat_id: str,
    user_message: ChatMessage,
    chat_memory: ChatMemoryBuffer,
) -> AsyncGenerator[str, None]:
    """
    Asynchronously streams the response from a ReActAgent as Server-Sent Events (SSE) while saving the conversation to the database.

    Args:
        agent (ReActAgent): The agent responsible for generating responses.
        user_input (str): The user's input message.
        db_client (SessionDep): Database session dependency for ORM operations.
        chat_id (str): The unique identifier for the chat session.
        user_message (ChatMessage): The user's message object to be saved.
        chat_memory (ChatMemoryBuffer): The memory buffer containing chat history.

    Yields:
        str: Server-Sent Event (SSE) formatted strings containing response chunks, status, or error messages.

    Raises:
        None: All exceptions are handled internally and streamed as error events.

    Side Effects:
        - Streams response chunks to the client as SSE.
        - Saves both user and assistant messages to the database after streaming is complete.
        - Logs errors and warnings related to streaming and database operations.
    """
    full_response_text = ""
    async_generator = None
    try:
        async_generator = agent.run(user_msg=user_input, memory=chat_memory)

        async for chunk in async_generator.stream_events():
            delta = None
            if hasattr(chunk, "delta") and chunk.delta:
                delta = chunk.delta
            elif isinstance(chunk, str):  # Handle simpler cases if agent streams raw strings
                delta = chunk

            if delta:
                full_response_text += delta
                # Format as Server-Sent Event (SSE)
                yield f"data: {json.dumps({'value': delta})}\n\n"
                await asyncio.sleep(0.1)

        # Some agent implementations may complete without delta events.
        if not full_response_text and async_generator is not None:
            try:
                final_response = await async_generator
                final_text = None
                if isinstance(final_response, str):
                    final_text = final_response
                elif hasattr(final_response, "response") and final_response.response:
                    final_text = final_response.response

                if final_text:
                    full_response_text = str(final_text)
                    yield f"data: {json.dumps({'value': full_response_text})}\n\n"
            except Exception as final_err:
                logger.warning(f"Could not resolve final agent response for chat {chat_id}: {final_err}")

        # Signal the end of the stream
        yield f"data: {json.dumps({'status': 'done'})}\n\n"

    except Exception as e:
        logger.error(f"Error during agent streaming for chat {chat_id}: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': 'An error occurred during streaming.'})}\n\n"
        full_response_text += "\n\n[Error during generation]"
    finally:
        # Save the Assistant's full message AFTER streaming is complete
        if full_response_text:
            assistant_message = ChatMessage(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                text=full_response_text.strip(),
                block_type="text",
                additional_kwargs={},
                chat_id=chat_id,
                created_at=datetime.now(),
            )
            messages = [
                user_message,
                assistant_message,
            ]
            try:
                db_chat = db_client.get(Chat, chat_id)
                if db_chat:
                    for chat_message in messages:
                        db_chat.messages.append(chat_message)

                    db_chat.last_interacted_at = datetime.now()
                    db_client.commit()
                    db_client.refresh(db_chat)
                    logger.info(f"Assistant message saved for chat {chat_id}")
                else:
                    logger.error(f"Chat {chat_id} not found when trying to save assistant message.")

            except Exception as db_error:
                logger.error(
                    f"Failed to save assistant message for chat {chat_id}: {db_error}",
                    exc_info=True,
                )
                db_client.rollback()
        else:
            logger.warning(f"No response generated for chat {chat_id}, not saving assistant message.")


@router.get("/", response_model=Page[ChatPublic])
async def get_all_chats(
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Retrieve all chats for the authenticated user.

    This endpoint fetches all chats associated with the authenticated user,
    ordered by the last interaction timestamp in descending order.

    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.

    **Returns**:
    - A paginated list of chats.

    **Raises**:
    - 404: If the session ID is not found in cookies or the user is not authenticated.
    """
    query = db_client.query(Chat)
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.error("Session id not found in cookies")
        raise HTTPException(status_code=404, detail="Not found")
    token = redis_client.get(f"session:{session_id}")
    claims = decode_jwt(token)
    user_id = claims["oid"]
    query = query.filter(Chat.user_id == user_id).order_by(Chat.last_interacted_at.desc())
    page = sqlalchemy_pagination(query)
    return page


@router.get("/search")
async def get_chats_by_title(
    title: str,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Search chats by title for the authenticated user.

    This endpoint allows the user to search for chats by their title.

    - **title**: The title or partial title of the chat to search for.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.

    **Returns**:
    - A list of chats matching the title.

    **Raises**:
    - 404: If the session ID is not found in cookies or the user is not authenticated.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.error("Session id not found in cookies")
        raise HTTPException(status_code=404, detail="Not found")
    token = redis_client.get(f"session:{session_id}")
    claims = decode_jwt(token)
    user_id = claims["oid"]
    chats = db_client.query(Chat).filter(Chat.title.like(f"%{title}%")).filter(Chat.user_id == user_id).all()

    return chats


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Retrieve a specific chat by its ID.

    This endpoint fetches a chat and its associated messages for the authenticated user.

    - **chat_id**: The unique identifier of the chat.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.

    **Returns**:
    - The chat details, including files, messages, and favorite status.

    **Raises**:
    - 404: If the chat is not found or does not belong to the user.
    """
    db_chat = db_client.get(Chat, chat_id)
    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user = check_property_belongs_to_user(request, redis_client, db_chat)
    messages = (
        db_client.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.desc())
        .all()
    )[:10]

    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat not found")

    # Get favorite status
    favorite = db_chat.favourite if db_chat.favourite else None

    return {
        **serialize_chat(db_chat, include_files=True),
        "messages": [serialize_chat_message(message) for message in messages],
        "favourite": serialize_favourite(favorite),
    }


@router.post("/{chat_id}/chat/stream")
async def chat_stream(
    chat_id: str,
    chat: ChatQuery,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
    chroma_vector_store: ChromaVectorStore = Depends(get_chroma_vector),
):
    """
    Handles the chat streaming endpoint for a specific chat session.

    This endpoint allows users to send a chat query and receive a streaming response
    from the chat agent. It validates the chat session, checks user permissions, and
    processes the chat query using a language model and associated tools.

    Args:
        chat_id (str): The unique identifier of the chat session.
        chat (ChatQuery): The chat query object containing the user's input text.
        db_client (Session): Database session dependency for interacting with the database.
        request (Request): The HTTP request object.
        redis_client (Redis): Redis client dependency for caching and session management.
        chroma_vector_store (ChromaVectorStore): Dependency for vector-based storage and retrieval.

    Raises:
        HTTPException: If the chat parameter is missing.
        HTTPException: If the chat session is not found in the database.
        HTTPException: If the chat session does not belong to the authenticated user.

    Returns:
        StreamingResponse: A streaming response containing the chat agent's output in
        "text/event-stream" format.
    """
    if not chat:
        logger.error("Missing chat parameter")
        raise HTTPException(status_code=404, detail="Body: text is required")

    db_chat = db_client.get(Chat, chat_id)
    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user = check_property_belongs_to_user(request, redis_client, db_chat)
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        role=MessageRole.USER,
        text=chat.text,
        block_type="text",
        additional_kwargs={},
        chat_id=chat_id,
        created_at=datetime.now(),
    )

    old_messages = (
        db_client.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.desc())
        .all()
    )[:25]

    chat_history = [
        LLMChatMessage(
            role=message.role,
            content=message.text,
            additional_kwargs=message.additional_kwargs,
        )
        for message in old_messages
    ]

    tools: list[BaseTool] = []
    files = db_chat.files

    if db_chat.model:
        model_from_chat = db_chat.model
    else:
        model_from_chat = "llama3.3:70b"

    provider = (db_chat.model_provider or "GOOGLE_GENAI").upper()
    llm = None

    if provider == "OLLAMA":
        llm = Ollama(
            model=model_from_chat,
            temperature=db_chat.temperature,
            request_timeout=500,
            base_url=base_url,
        )
    elif provider == "IONOS":
        llm = initialize_ionos_llm(temperature=db_chat.temperature)
    elif provider == "GOOGLE_GENAI":
        from llama_index.llms.google_genai import GoogleGenAI

        llm = GoogleGenAI(model=model_from_chat, temperature=db_chat.temperature)

    # Fall back to globally configured LLM (e.g. GOOGLE provider from app startup).
    if llm is None:
        llm = Settings.llm

    if llm is None:
        logger.error("No LLM configured for chat stream (provider=%s)", provider)
        raise HTTPException(status_code=500, detail="No LLM configured. Check server model settings.")

    # new implementation of agent memory
    chat_memory = create_memory(
        chat_id=chat_id,
        llm=llm,
        messages=chat_history,
        vector_store=chroma_vector_store,
        token_limit=128_000,
        system_prompt=db_chat.context,
    )

    for file_id, file_params in chat.params.files.items():
        files_to_query = [file for file in files if file.id == file_id and file_params.queried == True]
        query_engine_tools = create_query_engine_tools(
            files=files_to_query,
            chroma_vector_store=chroma_vector_store,
            llm=llm,
            params=file_params,
        )
        if len(query_engine_tools) > 0:
            tools += query_engine_tools
        for file in files_to_query:
            if file.id == file_id and file_params.query_type == "sql":
                sql_tools = create_sql_engines_tools_from_files(
                    files=files_to_query, chroma_vector_store=chroma_vector_store
                )
                tools += sql_tools
            if file.id == file_id and file_params.query_type == "spreadsheet":
                pd_tools = create_pandas_engines_tools_from_files(files=files_to_query)
                tools += pd_tools

    if chat.params.use_link_scraping:
        scrape_tool = create_url_loader_tool(chroma_vector_store=chroma_vector_store, chat=db_chat)
        tools.append(scrape_tool)
    if chat.params.use_websearch:
        search_engine_tool = create_search_engine_tool(chroma_vector_store=chroma_vector_store, chat=db_chat)
        tools.append(search_engine_tool)

    agent = create_agent(system_prompt=db_chat.context, tools=tools, llm=llm)
    streaming_generator = stream_agent_response(
        agent=agent,
        user_input=chat.text,
        db_client=db_client,
        chat_id=db_chat.id,
        user_message=user_message,
        chat_memory=chat_memory,
    )

    return StreamingResponse(streaming_generator, media_type="text/event-stream")


@router.post("/{chat_id}/chat")
async def chat_with_given_chat_id(
    chat_id: str,
    chat: ChatQuery,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
    chroma_vector_store: ChromaVectorStore = Depends(get_chroma_vector),
):
    """
    Interact with a specific chat by sending a message.

    This endpoint allows the user to send a message to a chat and receive a response
    from the chat agent.

    - **chat_id**: The unique identifier of the chat.
    - **chat**: The message query object containing the user's input.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.
    - **chroma_vector_store**: Dependency for vector store operations.

    **Returns**:
    - The updated chat details and the assistant's response.

    **Raises**:
    - 404: If the chat is not found or does not belong to the user.
    """
    if not chat:
        logger.error("Missing chat parameter")
        raise HTTPException(status_code=404, detail="Body: text is required")

    db_chat = db_client.get(Chat, chat_id)
    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user = check_property_belongs_to_user(request, redis_client, db_chat)
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        role=MessageRole.USER,
        text=chat.text,
        block_type="text",
        additional_kwargs={},
        chat_id=chat_id,
        created_at=datetime.now(),
    )

    old_messages = (
        db_client.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.desc())
        .all()
    )[:25]

    chat_history = [
        LLMChatMessage(
            role=message.role,
            content=message.text,
            additional_kwargs=message.additional_kwargs,
        )
        for message in old_messages
    ]

    # Now the fun is getting started
    chat_memory = ChatMemoryBuffer.from_defaults(
        chat_history=chat_history,
        token_limit=128_000,
    )

    files = db_chat.files
    tools = create_query_engine_tools(files=files, chroma_vector_store=chroma_vector_store)
    pd_tools = create_pandas_engines_tools_from_files(files=files)
    sql_tools = create_sql_engines_tools_from_files(files=files, chroma_vector_store=chroma_vector_store)

    scrape_tool = create_url_loader_tool(chroma_vector_store=chroma_vector_store, chat=db_chat)
    search_engine_tool = create_search_engine_tool(chroma_vector_store=chroma_vector_store, chat=db_chat)

    tools = tools + pd_tools
    tools = tools + sql_tools
    tools = tools + [scrape_tool]
    tools = tools + [search_engine_tool]

    if db_chat.model:
        model_from_chat = db_chat.model
    else:
        model_from_chat = "llama3.3:70b"

    llm = Ollama(
        model=model_from_chat,
        temperature=db_chat.temperature,
        request_timeout=500,
        base_url=base_url,
    )
    agent = create_agent(
        memory=chat_memory,
        system_prompt=PromptTemplate(db_chat.context),
        tools=tools,
        llm=llm,
    )
    agent_response: AgentChatResponse = await agent.achat(chat.text)

    db_chat.last_interacted_at = datetime.now()
    chat_messages = [
        user_message,
        ChatMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            text=agent_response.response,
            block_type="text",
            additional_kwargs={},
            chat_id=chat_id,
            created_at=datetime.now(),
        ),
    ]
    for chat_message in chat_messages:
        db_chat.messages.append(chat_message)
    db_client.add(db_chat)
    db_client.commit()
    db_client.refresh(db_chat)

    return {
        **serialize_chat(db_chat),
        "message": {"response": agent_response, "role": "assistant"},
    }


@router.post("/{chat_id}/upload")
async def upload_file_to_chat(
    chat_id: str,
    file: UploadFile = File(...),
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    chroma_collection: Collection = Depends(get_chroma_collection),
    redis_session: Redis = Depends(get_redis_client),
    background_tasks: BackgroundTasks = BackgroundTasks,
):
    """
    Upload a file to a specific chat.

    This endpoint allows the user to upload a file to a chat. If the file is an SQL dump,
    it will be processed and indexed in the background.

    - **chat_id**: The unique identifier of the chat.
    - **file**: The file to be uploaded.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **chroma_collection**: Dependency for vector store operations.
    - **redis_session**: Redis client dependency for session validation.
    - **background_tasks**: Background task manager for processing SQL dumps.

    **Returns**:
    - The updated chat details, including the uploaded file.

    **Raises**:
    - 404: If the chat is not found, does not belong to the user, or the file already exists.
    - 500: If an error occurs during file processing or indexing.
    """
    db_chat = db_client.get(Chat, chat_id)
    # Check if chat exists, if exists, continue
    if not db_chat:
        logger.error("Chat not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user, user_id = check_property_belongs_to_user(request, redis_session, db_chat)
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")
    # If file is not attached to Upload, raise Error
    if not file.filename:
        logger.error("Does not have a File")
        raise HTTPException(status_code=404, detail="File not found")
    # If file is already uploaded, raise Error
    for chat_file in db_chat.files:
        if chat_file.file_name == file.filename:
            logger.error(f"File already uploaded {file.filename}")
            raise HTTPException(status_code=404, detail="File already exists")
    # Upload file to Folder and persist it
    chat_folder = BASE_UPLOAD_DIR / f"{chat_id}"
    chat_folder.mkdir(parents=True, exist_ok=True)
    file_path = chat_folder / f"{file.filename}"
    with open(file_path, "wb+") as buffer:
        buffer.write(file.file.read())
    db_file = ChatFile(
        id=str(uuid.uuid4()),
        chat_id=db_chat.id,
        path_name=str(file_path),
        mime_type=file.content_type,
        file_name=file.filename,
        indexed=None
        if any(
            ext in file.content_type.lower() or ext in file.filename.lower()
            for ext in ["sql", "xlsx", "spreadsheet", "csv"]
        )
        else False,
    )

    if file.content_type.lower().find("sql") != -1 and db_chat is not None:
        logger.info(f"Processing SQL File for Chat: {db_chat.id}")
        database_name = f"sd_{db_chat.id.replace('-', '_')[:5]}_{time.time_ns()}"
        db_file.database_name = database_name
        database_type = detect_sql_dump_type(str(file_path))
        db_file.database_type = database_type
        background_tasks.add_task(
            process_dump_to_persist,
            db_client=db_client,
            chat_id=chat_id,
            sql_dump_path=str(file_path),
            database_type=database_type,
            chat_file_id=db_file.id,
            db_name=database_name,
            chroma_collection=chroma_collection,
        )

    try:
        # indexes file
        db_chat.last_interacted_at = datetime.now()
        db_chat.files.append(db_file)
        db_client.commit()

        if not any(
            ext in file.content_type.lower() or ext in file.filename.lower()
            for ext in ["sql", "xlsx", "spreadsheet", "csv"]
        ):
            background_tasks.add_task(
                index_uploaded_file,
                path=str(file_path),
                chat_file=db_file,
                chroma_collection=chroma_collection,
                db_client=db_client,
            )
        if any(
            ext in file.content_type.lower() or ext in file.filename.lower() for ext in ["xlsx", "spreadsheet", "csv"]
        ):
            md_id = str(uuid.uuid4())
            md_file_path = f"{os.getcwd()}/uploads/{db_chat.id}/{file.filename.split('.')[0]}.md"
            md_file = ChatFile(
                id=md_id,
                file_name=f"{db_file.file_name.split('.')[0]}.md",
                path_name=md_file_path,
                indexed=False,
                chat_id=chat_id,
                mime_type="text/markdown",
            )
            try:
                db_chat.files.append(md_file)
                db_client.commit()
                logger.info(f"Created temporary markdown file, that is not indexed yet: {md_file.file_name}")
            except Exception as e:
                logger.error(e)
                db_client.rollback()
            background_tasks.add_task(
                index_spreadsheet,
                chroma_collection=chroma_collection,
                file=db_file,
                db_client=db_client,
            )
        db_client.refresh(db_chat)
        return {
            **serialize_chat(db_chat, include_files=True),
        }
    except Exception as e:
        db_client.rollback()
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_chat(
    chat: str = Form(...),
    file: UploadFile | None = None,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Create a new chat.

    This endpoint allows the user to create a new chat. Optionally, an avatar image
    can be uploaded for the chat.

    - **chat**: The chat data in JSON format.
    - **file**: Optional avatar image file.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.

    **Returns**:
    - The created chat details.

    **Raises**:
    - 404: If the session ID is not found in cookies.
    - 400: If the avatar image format is invalid.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.error("Session id cookie not found")
        raise HTTPException(status_code=404, detail="Session not found")

    token = redis_client.get(f"session:{session_id}")
    claims = decode_jwt(token)
    user_id = claims["oid"]

    chat_id = str(uuid.uuid4())
    avatar_path = None

    if file and file.filename:
        # Get file extension
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "gif"]:
            logger.error("Invalid image format for chat avatar")
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Create avatars directory if it doesn't exist
        avatar_dir = BASE_UPLOAD_DIR / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        avatar_path = avatar_dir / f"{chat_id}.{ext}"
        with open(avatar_path, "wb+") as buffer:
            buffer.write(file.file.read())

    chat_data = json.loads(chat)
    db_chat = Chat(**chat_data, user_id=user_id, id=chat_id, avatar_path=str(avatar_path))

    try:
        db_client.add(db_chat)
        db_client.commit()
        db_client.refresh(db_chat)
    except Exception as e:
        logger.error(e)
        db_client.rollback()
        return Response(status_code=500, content="Chat create error.")

    return {
        **serialize_chat(db_chat, include_files=True),
    }


@router.put("/{chat_id}")
async def update_chat(
    chat_id: str,
    chat: str = Form(...),
    file: UploadFile = File(None),
    request: Request = Request,
    db_client: SessionDep = SessionDep,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Update an existing chat.

    This endpoint allows the user to update the details of an existing chat. Optionally,
    a new avatar image can be uploaded.

    - **chat_id**: The unique identifier of the chat.
    - **chat**: The updated chat data in JSON format.
    - **file**: Optional new avatar image file.
    - **request**: HTTP request object to extract cookies.
    - **db_client**: Database session dependency.
    - **redis_client**: Redis client dependency for session validation.

    **Returns**:
    - The updated chat details.

    **Raises**:
    - 404: If the chat is not found or does not belong to the user.
    - 400: If the avatar image format is invalid.
    """
    db_chat = db_client.get(Chat, chat_id)
    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user = check_property_belongs_to_user(request, redis_client, db_chat)
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    avatar_path = None

    if file and file.filename:
        # Get file extension
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
            logger.error("Invalid image format for chat avatar")
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Create avatars directory if it doesn't exist
        avatar_dir = BASE_UPLOAD_DIR / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)

        # Save new file
        avatar_path = avatar_dir / f"{chat_id}.{ext}"
        with open(avatar_path, "wb+") as buffer:
            buffer.write(file.file.read())

    # Update mutable chat fields explicitly (SQLAlchemy model, no sqlmodel_update helper).
    chat_data = json.loads(chat)
    updatable_fields = {
        "title",
        "description",
        "context",
        "temperature",
        "model",
        "model_provider",
    }
    for field_name in updatable_fields:
        if field_name in chat_data:
            setattr(db_chat, field_name, chat_data[field_name])
    if avatar_path:
        db_chat.avatar_path = str(avatar_path)

    db_chat.last_interacted_at = datetime.now()
    db_client.add(db_chat)
    db_client.commit()
    db_client.refresh(db_chat)

    return {
        **serialize_chat(db_chat, include_files=True),
    }


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
    chroma_collection: Collection = Depends(get_chroma_collection),
):
    """
    Delete a chat.

    This endpoint allows the user to delete a chat and all its associated files,
    messages, and avatar.

    - **chat_id**: The unique identifier of the chat.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.
    - **chroma_collection**: Dependency for vector store operations.

    **Returns**:
    - The deleted chat details.

    **Raises**:
    - 404: If the chat is not found or does not belong to the user.
    """
    db_chat = db_client.get(Chat, chat_id)
    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user = check_property_belongs_to_user(request, redis_client, db_chat)
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    files = db_chat.files
    for _file in files:
        deletes_file_index_from_collection(file_id=_file.id, chroma_collection=chroma_collection)

    # Get chat folder path and delete all files inside
    chat_folder = BASE_UPLOAD_DIR / str(chat_id)
    if chat_folder.exists():
        for file in chat_folder.iterdir():
            file.unlink()  # Delete each file
        chat_folder.rmdir()  # Remove the folder itself

    # Delete avatar file if it exists
    if db_chat.avatar_path and Path(db_chat.avatar_path).exists():
        Path(db_chat.avatar_path).unlink()

    db_client.delete(db_chat)
    db_client.commit()
    return {
        **serialize_chat(db_chat),
    }


@router.delete("/{chat_id}/delete/{file_id}")
async def delete_file_of_chat(
    chat_id: str,
    file_id: str,
    db_client: SessionDep = SessionDep,
    request: Request = Request,
    redis_client: Redis = Depends(get_redis_client),
    chroma_collection: Collection = Depends(get_chroma_collection),
):
    """
    Delete a file from a chat.

    This endpoint allows the user to delete a specific file from a chat. If the file
    is an SQL dump, the associated database will also be deleted.

    - **chat_id**: The unique identifier of the chat.
    - **file_id**: The unique identifier of the file.
    - **db_client**: Database session dependency.
    - **request**: HTTP request object to extract cookies.
    - **redis_client**: Redis client dependency for session validation.
    - **chroma_collection**: Dependency for vector store operations.

    **Returns**:
    - The updated chat details after file deletion.

    **Raises**:
    - 404: If the chat or file is not found, or the file does not belong to the chat.
    """
    # If chat is not existing, raise Error
    db_chat = db_client.get(Chat, chat_id)
    if not db_chat:
        logger.error(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    belongs_to_user = check_property_belongs_to_user(request, redis_client, db_chat)
    if not belongs_to_user:
        logger.error(f"Chat {chat_id} does not belong to user")
        raise HTTPException(status_code=404, detail="Chat does not belong to user")

    # If file is not existing or does not belong to Chat, raise Error
    db_file = db_client.get(ChatFile, file_id)
    if not db_file or db_file.chat_id != chat_id:
        logger.error(f"{db_file.file_name} not found or does not belong to Chat")
        raise HTTPException(status_code=404, detail="File not found or does not belong to this chat")

    # Construct file path and delete from disk
    file_path = BASE_UPLOAD_DIR / str(chat_id) / db_file.file_name
    if file_path.exists():
        file_path.unlink()  # Delete file from storage

    if db_file.mime_type.find("sql") != -1:
        # delete sql database
        delete_database_from_postgres(db_file.database_name)
    else:
        # deletes index from DB
        deletes_file_index_from_collection(chroma_collection=chroma_collection, file_id=db_file.id)
    # Remove file record from the database
    db_client.delete(db_file)
    db_chat.last_interacted_at = datetime.now()
    db_client.commit()
    db_client.refresh(db_chat)

    return {
        **serialize_chat(db_chat, include_files=True),
    }
