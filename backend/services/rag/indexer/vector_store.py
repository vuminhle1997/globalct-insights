from typing import override

from llama_index.core import VectorStoreIndex


class StrictVectorStoreIndex(VectorStoreIndex):
    """
    A custom VectorStoreIndex that enforces the presence of filters when creating a query engine.
    This is designed to ensure that the index is used in a way that aligns with the intended use case
    of being part of a RAG system where specific filtering is necessary for effective retrieval.
    """

    @override
    def as_query_engine(self, filters=None, **kwargs):
        """
        Override the as_query_engine method to enforce that filters must be provided.
        This ensures that the query engine is always used with specific filters, which is
        important for the intended use case of this index in the RAG system.
        """
        if filters is None:
            raise ValueError("Filters must be provided for StrictVectorStoreIndex.")
        return super().as_query_engine(filters=filters, **kwargs)

    @classmethod
    @override
    def from_vector_store(cls, vector_store, embed_model=None, **kwargs) -> "StrictVectorStoreIndex":
        """
        Override the from_vector_store class method to ensure that the created index is an instance
        of StrictVectorStoreIndex.
        This ensures that any index created from a vector store will have the strict filter enforcement behavior.
        """
        return super().from_vector_store(vector_store, embed_model, **kwargs)
