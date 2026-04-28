from collections.abc import Sequence
from typing import Any

from llama_index.core.llms import LLM, ChatMessage as LLMChatMessage
from llama_index.core.memory import (
    FactExtractionMemoryBlock,
    Memory,
    StaticMemoryBlock,
    VectorMemoryBlock,
)
from llama_index.core.settings import Settings
from llama_index.vector_stores.chroma import ChromaVectorStore

DEFAULT_MAX_TOKEN_LIMIT = 128_000  # Aligns with planned usage of 128K-context OSS / frontier models.


def create_memory(
    chat_id: str,
    llm: LLM | None,
    messages: Sequence[LLMChatMessage] | None = None,
    vector_store: ChromaVectorStore | None = None,
    *,
    token_limit: int = DEFAULT_MAX_TOKEN_LIMIT,
    chat_history_token_ratio: float = 0.3,
    token_flush_size: int | None = None,
    max_facts: int = 25,
    similarity_top_k: int = 5,
    retrieval_context_window: int = 6,
    system_prompt: str = (
        "You are a smart AI assistant. Follow system instructions and user-provided rules faithfully."
    ),
) -> Memory:
    """Create and initialize conversational memory for an agent.

    This function assembles several memory blocks (static, fact extraction, optional vector memory)
    and returns a unified ``Memory`` object pre-populated with prior chat history.

    Parameters
    ----------
    chat_id : str
        Unique session identifier (also used as memory session_id).
    llm : LLM | None
        The language model used for fact extraction and downstream reasoning.
        If None, falls back to ``Settings.llm``.
    messages : Sequence[LLMChatMessage], optional
        Historical messages to seed the memory. If None or empty, seeding is skipped.
    vector_store : ChromaVectorStore, optional
        Backing vector store for semantic recall. If not provided, vector block is omitted.
    token_limit : int, default 128_000
        Hard cap for combined token budget (history + blocks). Tune per model context window.
    chat_history_token_ratio : float, default 0.3
        Fraction of token budget reserved for short-term rolling chat history.
    token_flush_size : int, optional
        Chunk size for flushing / trimming tokens. Defaults to max(1024, int(token_limit * 0.01)).
    max_facts : int, default 25
        Maximum retained atomic facts in the fact extraction block.
    similarity_top_k : int, default 5
        Top-k semantic batches to retrieve from vector memory.
    retrieval_context_window : int, default 6
        How many previous messages to include when forming a semantic retrieval query.
    system_prompt : str
        Static guidance injected via the ``StaticMemoryBlock``.

    Returns
    -------
    Memory
        Configured memory instance ready for agent consumption.

    Notes
    -----
    - Keeps backward compatibility with prior signature (parameters now optional / keyword-only).
    - Vector block is only constructed if a vector_store is supplied and an embedding model is set.
    - Add a debug helper ``memory_debug_snapshot`` for inspection.
    """
    if not chat_id:
        raise ValueError("chat_id must be a non-empty string")

    if token_limit <= 0:
        raise ValueError("token_limit must be positive")

    if llm is None:
        llm = Settings.llm
    if llm is None:
        raise RuntimeError("No LLM configured for memory creation. Pass an llm explicitly or set Settings.llm.")

    # Derive default flush size adaptively if not provided.
    if token_flush_size is None:
        token_flush_size = max(1024, int(token_limit * 0.01))

    blocks: list[Any] = []

    # Static/system prompt block (priority 0 => always retained first)
    blocks.append(
        StaticMemoryBlock(
            name="core_info",
            static_content=system_prompt,
            priority=0,
        )
    )

    # Fact extraction block (captures distilled facts from dialog)
    blocks.append(
        FactExtractionMemoryBlock(
            name="extracted_info",
            llm=llm,
            max_facts=max_facts,
            priority=1,
        )
    )

    # Vector semantic recall (optional)
    if vector_store is not None:
        if Settings.embed_model is None:
            raise RuntimeError(
                "Settings.embed_model is None; an embedding model must be configured before enabling vector memory."
            )
        blocks.append(
            VectorMemoryBlock(
                name="vector_memory",
                vector_store=vector_store,
                priority=2,
                embed_model=Settings.embed_model,
                similarity_top_k=similarity_top_k,  # Number of semantic batches to pull
                retrieval_context_window=retrieval_context_window,  # Previous messages added to query
            )
        )

    memory = Memory.from_defaults(
        token_limit=token_limit,
        memory_blocks=blocks,
        session_id=chat_id,
        chat_history_token_ratio=chat_history_token_ratio,
        token_flush_size=token_flush_size,
    )

    if messages:
        memory.put_messages(list(messages))

    return memory


def memory_debug_snapshot(memory: Memory) -> dict:
    """Return a lightweight diagnostic snapshot of the memory state.

    Includes counts and sample content without exposing full internal objects.
    Safe to serialize for logging.
    """
    snapshot = {
        "session_id": getattr(memory, "session_id", None),
        "token_limit": getattr(memory, "token_limit", None),
        "chat_history_len": len(getattr(memory, "chat_history", []) or []),
        "blocks": [],
    }
    for blk in getattr(memory, "memory_blocks", []):
        blk_info = {"name": getattr(blk, "name", None), "type": blk.__class__.__name__}
        if isinstance(blk, FactExtractionMemoryBlock):
            blk_info["fact_count"] = len(getattr(blk, "facts", []) or [])
        snapshot["blocks"].append(blk_info)
    return snapshot
