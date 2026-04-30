import asyncio
import json
import os
import re
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

from chromadb import Collection
from fastapi import BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.llms import MessageRole
from llama_index.vector_stores.chroma import ChromaVectorStore
from redis import Redis
from starlette.requests import Request

from backend.core.serializers import serialize_chat, serialize_chat_file
from backend.dependencies import (
    SessionDep,
    get_chroma_collection,
    get_chroma_vector,
    get_redis_client,
    logger,
)
from backend.models.chat import Chat, ChatQuery
from backend.models.chat_file import ChatFile
from backend.models.chat_message import ChatMessage
from backend.routers.custom_router import APIRouter
from backend.services.chat_service import build_chat_history, build_tools_from_params, resolve_llm_for_chat
from backend.services.indexer import index_spreadsheet, index_uploaded_file
from backend.services.llm_agent import create_agent
from backend.services.memory import create_memory
from backend.services.tasks import process_dump_to_persist
from backend.utils.check_property import check_property_belongs_to_user
from backend.utils.upload_sql_dump import detect_sql_dump_type

BASE_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    prefix="/chats",
    tags=["chats"],
    responses={404: {"description": "Not found"}},
)


async def stream_agent_response(
    agent: ReActAgent,
    user_input: str,
    db_client: SessionDep,
    chat_id: str,
    user_message: ChatMessage,
    chat_memory,
) -> AsyncGenerator[str, None]:
    """
    Asynchronously streams the response from a ReActAgent as Server-Sent Events (SSE) while saving the conversation to the database.

    Args:
        agent (ReActAgent): The agent responsible for generating responses.
        user_input (str): The user's input message.
        db_client (SessionDep): Database session dependency for ORM operations.
        chat_id (str): The unique identifier for the chat session.
        user_message (ChatMessage): The user's message object to be saved.
        chat_memory: The memory instance containing chat history.

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

    belongs_to_user, _ = check_property_belongs_to_user(request, redis_client, db_chat)
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

    chat_history = build_chat_history(old_messages)

    llm = resolve_llm_for_chat(db_chat)

    # new implementation of agent memory
    chat_memory = create_memory(
        chat_id=chat_id,
        llm=llm,
        messages=chat_history,
        vector_store=chroma_vector_store,
        token_limit=128_000,
        system_prompt=db_chat.context,
    )

    tools = build_tools_from_params(
        files=db_chat.files,
        chat_params=chat.params,
        chroma_vector_store=chroma_vector_store,
        llm=llm,
        db_chat=db_chat,
    )

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

    belongs_to_user, _ = check_property_belongs_to_user(request, redis_client, db_chat)
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

    chat_history = build_chat_history(old_messages)

    llm = resolve_llm_for_chat(db_chat)

    # new implementation of agent memory
    chat_memory = create_memory(
        chat_id=chat_id,
        llm=llm,
        messages=chat_history,
        vector_store=chroma_vector_store,
        token_limit=128_000,
        system_prompt=db_chat.context,
    )

    tools = build_tools_from_params(
        files=db_chat.files,
        chat_params=chat.params,
        chroma_vector_store=chroma_vector_store,
        llm=llm,
        db_chat=db_chat,
    )

    agent = create_agent(system_prompt=db_chat.context, tools=tools, llm=llm)
    agent_response = await agent.run(user_msg=chat.text, memory=chat_memory)
    response_text = agent_response if isinstance(agent_response, str) else str(agent_response)

    db_chat.last_interacted_at = datetime.now()
    chat_messages = [
        user_message,
        ChatMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            text=response_text,
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
        "message": {"response": response_text, "role": "assistant"},
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
    # Validate chat_id is a well-formed UUID to prevent path traversal via path parameter
    _UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if not _UUID_RE.match(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat ID format")
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
    # Upload file to Folder and persist it — sanitize filename to prevent path traversal
    safe_filename = Path(file.filename).name
    chat_folder = BASE_UPLOAD_DIR / f"{chat_id}"
    chat_folder.mkdir(parents=True, exist_ok=True)
    file_path = chat_folder / safe_filename
    with open(file_path, "wb+") as buffer:
        buffer.write(file.file.read())
    db_file = ChatFile(
        id=str(uuid.uuid4()),
        chat_id=db_chat.id,
        path_name=str(file_path),
        mime_type=file.content_type,
        file_name=safe_filename,
        indexed=None
        if any(
            ext in file.content_type.lower() or ext in safe_filename.lower()
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
            ext in file.content_type.lower() or ext in safe_filename.lower()
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
            ext in file.content_type.lower() or ext in safe_filename.lower() for ext in ["sql", "xlsx", "spreadsheet", "csv"]
        ):
            md_id = str(uuid.uuid4())
            md_file_path = str(BASE_UPLOAD_DIR / db_chat.id / f"{safe_filename.split('.')[0]}.md")
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
