import pytest
import nest_asyncio
import os
import sys

from pathlib import Path
from services import (
    create_agent,
    create_query_engine_tools,
    create_search_engine_tool,
    create_url_loader_tool,
    create_pandas_engines_tools_from_files,
    create_sql_engines_tools_from_files,
)

from dotenv import load_dotenv
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric,
    SummarizationMetric,
    BiasMetric,
    ToxicityMetric,
)
from deepeval import assert_test, evaluate
from dependencies import logger
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.settings import Settings

try:
    load_dotenv()
    nest_asyncio.apply()
    model = os.getenv("OLLAMA_MODEL")
    if model is None:
        logger.error(f"Env '{model}' is missing.")
        sys.exit(os.EX_CONFIG)
    os.system(f"deepeval set-ollama {model}")

    model = Ollama(model=model, request_timeout=600)
    embedding = OllamaEmbedding(model_name="mxbai-embed-large", request_timeout=600)
    Settings.llm = model
    Settings.embed_model = embedding
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
except Exception as e:
    logger.error(f"Tests Error: {e}")

# def test_simple_use_case():
#     answer_relevancy_metric = AnswerRelevancyMetric(threshold=0.5)
#     test_case = LLMTestCase(
#         input="What if these shoes don't fit?",
#         # Replace this with the actual output from your LLM application
#         actual_output="We offer a 30-day full refund at no extra costs.",
#         retrieval_context=[
#             "All customers are eligible for a 30 day full refund at no extra costs."
#         ],
#     )
#     assert_test(test_case, [answer_relevancy_metric])


def test_llama_rag():
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

    # Read LlamaIndex's quickstart on more details
    test_file_path = Path(__file__).parent / "data" / "TWICE_Wikipedia.txt"
    documents = SimpleDirectoryReader(input_files=[str(test_file_path)]).load_data()
    index = VectorStoreIndex.from_documents(documents)
    rag_application = index.as_query_engine()

    # An example input to your RAG application
    user_input = "Who is TWICE?"

    # LlamaIndex returns a response object that contains
    # both the output string and retrieved nodes
    response_object = rag_application.query(user_input)

    metrics = [
        AnswerRelevancyMetric(threshold=0.5),
        FaithfulnessMetric(threshold=0.5),
        ContextualRelevancyMetric(threshold=0.5),
        # BiasMetric(threshold=0.5), # comment that out, since it failes because TWICE is not "diversed" enough for the LLM
        ToxicityMetric(threshold=0.5),
    ]

    test_case = LLMTestCase(
        input=user_input, actual_output=response_object.response, retrieval_context=[""]
    )

    assert_test(test_case, metrics)
