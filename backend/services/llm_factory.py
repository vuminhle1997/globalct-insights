import os

from dotenv import load_dotenv
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms import LLM

load_dotenv()


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
        If an unsupported provider string is given.
    """
    provider_upper = provider.upper()

    if provider_upper == "IONOS":
        from llama_index.llms.openai_like import OpenAILike

        ionos_base_url = base_url or os.getenv("IONOS_BASE_URL", "http://localhost:11434")
        api_key = os.getenv("IONOS_API_KEY", "your_api_key_here")
        os.environ["OPENAI_API_BASE"] = ionos_base_url
        os.environ["OPENAI_API_KEY"] = api_key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return OpenAILike(
            api_base=ionos_base_url,
            temperature=temperature,
            model=model or "meta-llama/Llama-3.3-70B-Instruct",
            is_chat_model=True,
            default_headers=headers,
            api_key=api_key,
            context_window=128000,
            request_timeout=420,
        )

    elif provider_upper == "OLLAMA":
        from llama_index.llms.ollama import Ollama

        ollama_host = os.getenv("OLLAMA_HOST", "localhost")
        ollama_port = os.getenv("OLLAMA_PORT", "11434")
        ollama_base_url = base_url or f"{ollama_host}:{ollama_port}"
        return Ollama(
            model=model or os.getenv("OLLAMA_MODEL", "llama3.1"),
            base_url=ollama_base_url,
            temperature=temperature,
            request_timeout=420,
        )

    elif provider_upper == "GOOGLE_GENAI":
        from llama_index.llms.google_genai import GoogleGenAI

        return GoogleGenAI(
            model=model or os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
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
        If an unsupported provider string is given.
    """
    provider_upper = provider.upper()

    if provider_upper == "IONOS":
        from llama_index.embeddings.openai import OpenAIEmbedding

        ionos_base_url = base_url or os.getenv("IONOS_BASE_URL", "http://localhost:11434")
        api_key = os.getenv("IONOS_API_KEY", "your_api_key_here")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return OpenAIEmbedding(
            model_name="BAAI/bge-m3",
            api_base=ionos_base_url,
            api_key=api_key,
            default_headers=headers,
            embed_batch_size=10,
        )

    elif provider_upper == "OLLAMA":
        from llama_index.embeddings.ollama import OllamaEmbedding

        ollama_host = os.getenv("OLLAMA_HOST", "localhost")
        ollama_port = os.getenv("OLLAMA_PORT", "11434")
        ollama_base_url = base_url or f"{ollama_host}:{ollama_port}"
        return OllamaEmbedding(
            model_name=os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large"),
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
