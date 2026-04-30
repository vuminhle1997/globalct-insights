from fastapi import HTTPException
from llama_index.core.llms import LLM, ChatMessage as LLMChatMessage
from llama_index.core.settings import Settings
from llama_index.core.tools import BaseTool
from llama_index.vector_stores.chroma import ChromaVectorStore

from backend.models.chat import Chat, ChatParams
from backend.models.chat_file import ChatFile
from backend.models.chat_message import ChatMessage
from backend.services.chat.chat_tools import (
    create_pandas_engines_tools_from_files,
    create_query_engine_tools,
    create_search_engine_tool,
    create_sql_engines_tools_from_files,
    create_url_loader_tool,
)
from backend.services.factory.llm_factory import create_llm


def resolve_llm_for_chat(db_chat: Chat) -> LLM:
    """
    Resolve the LLM from a Chat's model_provider and model fields.
    Falls back to Settings.llm if no provider is matched.
    Raises HTTPException(500) if no LLM is found.
    """
    model = db_chat.model or None
    provider = (db_chat.model_provider or "GOOGLE_GENAI").upper()
    llm = None
    if provider in ("OLLAMA", "IONOS", "GOOGLE_GENAI"):
        llm = create_llm(provider, model=model, temperature=db_chat.temperature)
    if llm is None:
        llm = Settings.llm
    if llm is None:
        raise HTTPException(status_code=500, detail="No LLM configured. Check server model settings.")
    return llm


def build_chat_history(db_messages: list[ChatMessage]) -> list[LLMChatMessage]:
    """Convert DB ChatMessage records to LlamaIndex ChatMessage objects."""
    return [
        LLMChatMessage(
            role=m.role,
            content=m.text,
            additional_kwargs=m.additional_kwargs,
        )
        for m in db_messages
    ]


def build_tools_from_params(
    files: list[ChatFile],
    chat_params: ChatParams,
    chroma_vector_store: ChromaVectorStore,
    llm: LLM,
    db_chat: Chat,
) -> list[BaseTool]:
    """
    Build the full list of BaseTool objects from ChatParams + files.
    Handles RAG tools, SQL tools, Pandas tools, URL scraping, and web search.
    """
    tools: list[BaseTool] = []
    for file_id, file_params in chat_params.files.items():
        files_to_query = [f for f in files if f.id == file_id and file_params.queried is True]
        query_engine_tools = create_query_engine_tools(
            files=files_to_query,
            chroma_vector_store=chroma_vector_store,
            llm=llm,
            params=file_params,
        )
        tools.extend(query_engine_tools)
        if files_to_query and file_params.query_type == "sql":
            tools.extend(
                create_sql_engines_tools_from_files(files=files_to_query, chroma_vector_store=chroma_vector_store)
            )
        if files_to_query and file_params.query_type == "spreadsheet":
            tools.extend(create_pandas_engines_tools_from_files(files=files_to_query))

    if chat_params.use_link_scraping:
        tools.append(create_url_loader_tool(chroma_vector_store=chroma_vector_store, chat=db_chat))
    if chat_params.use_websearch:
        tools.append(create_search_engine_tool(chroma_vector_store=chroma_vector_store, chat=db_chat))

    return tools
