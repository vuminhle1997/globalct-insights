import os

from dotenv import load_dotenv
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms import LLM

from backend.core.config import (
    GOOGLE_MODEL,
    IONOS_API_KEY,
    IONOS_BASE_URL,
    IONOS_DEFAULT_EMBED_MODEL,
    IONOS_DEFAULT_MODEL,
    OLLAMA_EMBED_MODEL,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_PORT,
)

load_dotenv()

_DEFAULT_REQUEST_TIMEOUT = 420  # seconds — generous timeout for large-context LLM calls


def create_llm(
    provider: str,
    model: str | None = None,
    temperature: float = 0.75,
    base_url: str | None = None,
) -> LLM:
    """Create an LLM instance based on provider string.

    Parameters
    ----------
    provider : str
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

        ionos_base_url = base_url or IONOS_BASE_URL
        api_key = IONOS_API_KEY
        if not api_key:
            raise ValueError("IONOS_API_KEY environment variable is required for the IONOS provider.")
        os.environ["OPENAI_API_BASE"] = ionos_base_url
        os.environ["OPENAI_API_KEY"] = api_key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return OpenAILike(
            api_base=ionos_base_url,
            temperature=temperature,
            model=model or IONOS_DEFAULT_MODEL,
            is_chat_model=True,
            default_headers=headers,
            api_key=api_key,
            context_window=128000,
            request_timeout=_DEFAULT_REQUEST_TIMEOUT,
        )

    elif provider_upper == "OLLAMA":
        from llama_index.llms.ollama import Ollama

        ollama_base_url = base_url or f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
        return Ollama(
            model=model or OLLAMA_MODEL,
            base_url=ollama_base_url,
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
            f"Unsupported LLM provider: '{provider}'. "
            "Supported providers: 'IONOS', 'OLLAMA', 'GOOGLE_GENAI'."
        )


def create_embed_model(
    provider: str,
    base_url: str | None = None,
) -> BaseEmbedding:
    """Create an embedding model based on provider string.

    Parameters
    ----------
    provider : str
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

        ionos_base_url = base_url or IONOS_BASE_URL
        api_key = IONOS_API_KEY
        if not api_key:
            raise ValueError("IONOS_API_KEY environment variable is required for the IONOS provider.")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return OpenAIEmbedding(
            model_name=IONOS_DEFAULT_EMBED_MODEL,
            api_base=ionos_base_url,
            api_key=api_key,
            default_headers=headers,
            embed_batch_size=10,
        )

    elif provider_upper == "OLLAMA":
        from llama_index.embeddings.ollama import OllamaEmbedding

        ollama_base_url = base_url or f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
        return OllamaEmbedding(
            model_name=OLLAMA_EMBED_MODEL,
            base_url=ollama_base_url,
        )

    elif provider_upper == "GOOGLE_GENAI":
        from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

        return GoogleGenAIEmbedding()

    else:
        raise ValueError(
            f"Unsupported embedding provider: '{provider}'. "
            "Supported providers: 'IONOS', 'OLLAMA', 'GOOGLE_GENAI'."
        )
