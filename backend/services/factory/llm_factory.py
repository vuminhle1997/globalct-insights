import os
from enum import StrEnum

from dotenv import find_dotenv, load_dotenv
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms import LLM

from backend.core.config import (
    EMBED_BATCH_SIZE,
    GOOGLE_EMBED_MODEL,
    GOOGLE_MODEL,
    IONOS_API_KEY,
    IONOS_BASE_URL,
    IONOS_DEFAULT_EMBED_MODEL,
    IONOS_DEFAULT_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
    OLLAMA_MODEL,
)

load_dotenv(find_dotenv())

_DEFAULT_REQUEST_TIMEOUT = 420  # seconds — generous timeout for large-context LLM calls


class LLMProvider(StrEnum):
    IONOS = "IONOS"
    OLLAMA = "OLLAMA"
    GOOGLE_GENAI = "GOOGLE_GENAI"


def create_llm(
    provider: LLMProvider,
    model: str | None = None,
    temperature: float = 0.75,
) -> LLM:
    """Create an LLM instance based on provider string.

    Parameters
    ----------
    provider : LLMProvider
        The LLM provider to use. Supported values: "IONOS", "OLLAMA", "GOOGLE_GENAI"
        (case-insensitive).
    model : str, optional
        Override the default model name for the selected provider.
    temperature : float, default 0.75
        Sampling temperature passed to the LLM.
    base_url : str, optional
        Override the base URL for the selected provider (IONOS / OLLAMA).

    Returns
    -------
    LLM
        A configured LlamaIndex LLM instance.

    Raises
    ------
    ValueError
        If an unsupported provider string is given, or a required API key is missing.
    """
    provider_upper = provider.upper()

    if provider_upper == "IONOS":
        from llama_index.llms.openai_like import OpenAILike

        if not IONOS_API_KEY:
            raise ValueError("IONOS_API_KEY environment variable is required for the IONOS provider.")
        os.environ["OPENAI_API_BASE"] = IONOS_BASE_URL
        os.environ["OPENAI_API_KEY"] = IONOS_API_KEY
        headers = {
            "Authorization": f"Bearer {IONOS_API_KEY}",
            "Content-Type": "application/json",
        }
        return OpenAILike(
            api_base=IONOS_BASE_URL,
            temperature=temperature,
            model=model or IONOS_DEFAULT_MODEL,
            is_chat_model=True,
            default_headers=headers,
            api_key=IONOS_API_KEY,
            context_window=128000,
            request_timeout=_DEFAULT_REQUEST_TIMEOUT,
        )

    elif provider_upper == "OLLAMA":
        from llama_index.llms.ollama import Ollama

        if not OLLAMA_BASE_URL:
            raise ValueError("OLLAMA_BASE_URL environment variable is required for the OLLAMA provider.")
        return Ollama(
            model=model or OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=temperature,
            request_timeout=_DEFAULT_REQUEST_TIMEOUT,
        )

    elif provider_upper == "GOOGLE_GENAI":
        from llama_index.llms.google_genai import GoogleGenAI

        return GoogleGenAI(
            model=model or GOOGLE_MODEL,
            temperature=temperature,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. Supported providers: 'IONOS', 'OLLAMA', 'GOOGLE_GENAI'."
        )


def create_embed_model(provider: LLMProvider) -> BaseEmbedding:
    """Create an embedding model based on provider string.

    Parameters
    ----------
    provider : LLMProvider
        The embedding provider to use. Supported values: "IONOS", "OLLAMA", "GOOGLE_GENAI"
        (case-insensitive).
    base_url : str, optional
        Override the base URL for providers that require it (IONOS / OLLAMA).

    Returns
    -------
    BaseEmbedding
        A configured LlamaIndex embedding model instance.

    Raises
    ------
    ValueError
        If an unsupported provider string is given, or a required API key is missing.
    """
    provider_upper = provider.upper()

    if provider_upper == "IONOS":
        from llama_index.embeddings.openai import OpenAIEmbedding

        if not IONOS_API_KEY:
            raise ValueError("IONOS_API_KEY environment variable is required for the IONOS provider.")
        headers = {
            "Authorization": f"Bearer {IONOS_API_KEY}",
            "Content-Type": "application/json",
        }
        return OpenAIEmbedding(
            model_name=IONOS_DEFAULT_EMBED_MODEL,
            api_base=IONOS_BASE_URL,
            api_key=IONOS_API_KEY,
            default_headers=headers,
            embed_batch_size=EMBED_BATCH_SIZE,
        )

    elif provider_upper == "OLLAMA":
        from llama_index.embeddings.ollama import OllamaEmbedding

        return OllamaEmbedding(
            base_url=OLLAMA_BASE_URL,
            model_name=OLLAMA_EMBED_MODEL,
            embed_batch_size=EMBED_BATCH_SIZE,
        )

    elif provider_upper == "GOOGLE_GENAI":
        from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

        return GoogleGenAIEmbedding(
            model_name=GOOGLE_EMBED_MODEL,
            embed_batch_size=100,
            timeout=_DEFAULT_REQUEST_TIMEOUT,
            retries=10,
            verbose=True,
        )

    else:
        raise ValueError(
            f"Unsupported embedding provider: '{provider}'. Supported providers: 'IONOS', 'OLLAMA', 'GOOGLE_GENAI'."
        )
