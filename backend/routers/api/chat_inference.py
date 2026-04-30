import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.llms import MessageRole
from llama_index.vector_stores.chroma import ChromaVectorStore
from redis import Redis
from starlette.requests import Request

from backend.core.serializers import serialize_chat, serialize_chat_file
from backend.dependencies import (
    SessionDep,
    get_chroma_vector,
    get_redis_client,
    logger,
)
from backend.models.chat import Chat, ChatQuery
from backend.models.chat_message import ChatMessage
from backend.routers.custom_router import APIRouter
from backend.services.chat_service import build_chat_history, build_tools_from_params, resolve_llm_for_chat
from backend.services.llm_agent import create_agent
from backend.services.memory import create_memory
from backend.utils.check_property import check_property_belongs_to_user

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
