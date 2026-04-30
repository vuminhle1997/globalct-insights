import uuid

import pandas as pd
from llama_index.core import SQLDatabase, StorageContext
from llama_index.core.indices.struct_store import SQLTableRetrieverQueryEngine
from llama_index.core.llms import LLM
from llama_index.core.objects import ObjectIndex, SQLTableNodeMapping, SQLTableSchema
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.settings import Settings
from llama_index.core.tools import FunctionTool, QueryEngineTool, ToolMetadata
from llama_index.core.vector_stores import ExactMatchFilter, FilterOperator, MetadataFilter, MetadataFilters
from llama_index.readers.web import BeautifulSoupWebReader
from llama_index.tools.duckduckgo import DuckDuckGoSearchToolSpec
from llama_index.vector_stores.chroma import ChromaVectorStore
from sqlalchemy import create_engine

from backend.dependencies import logger
from backend.models.chat import Chat, FileParams
from backend.models.chat_file import ChatFile
from backend.services.migration.db_migration_manager import initialize_pg_url
from backend.services.rag.indexer.vector_store import StrictVectorStoreIndex
from backend.services.rag.pandas.pandas_query_engine import PandasQueryEngine


def create_filters_for_files(files: list[ChatFile]):
    if len(files) == 0:
        return []
    filters = [
        MetadataFilters(
            filters=[
                ExactMatchFilter(
                    key="file_id",
                    value=file.id,
                )
            ]
        )
        for file in files
        if all(ext not in file.mime_type.lower() for ext in ["sql", "xlsx", "csv"])
    ]
    logger.info(f"Created metadata filters for {len(filters)} files.")
    logger.info(f"Filters: {filters}")
    return filters


def create_query_engines_from_filters(
    filters: list[MetadataFilters], chroma_vector_store: ChromaVectorStore, llm: LLM
) -> list[BaseQueryEngine]:
    storage_context = StorageContext.from_defaults(vector_store=chroma_vector_store)
    vector_index = StrictVectorStoreIndex.from_vector_store(
        vector_store=chroma_vector_store,
        storage_context=storage_context,
        embed_model=Settings.embed_model,
    )
    query_engines = [
        vector_index.as_query_engine(
            filters=meta_filters,
            llm=llm if llm is not None else Settings.llm,
            node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)],
        )
        for meta_filters in filters
    ]
    return query_engines


def create_query_engine_tools(
    files: list[ChatFile],
    chroma_vector_store: ChromaVectorStore,
    llm: LLM,
    params: dict[str, FileParams] = None,
) -> list[QueryEngineTool]:
    excluded_mime_keywords = ["sql", "xlsx", "csv"]
    # Filter out unwanted files
    filtered_files = [
        file for file in files if all(ext not in file.mime_type.lower() for ext in excluded_mime_keywords)
    ]

    # Create filters and query engines
    filters = create_filters_for_files(files=filtered_files)
    query_engines = create_query_engines_from_filters(filters=filters, chroma_vector_store=chroma_vector_store, llm=llm)

    query_engine_tools = []
    for i, query_engine in enumerate(query_engines):
        file = filtered_files[i]
        is_markdown = file.mime_type.lower() == "text/markdown"

        description = (
            f"Query engine for deeply analyzing the markdown document '{file.file_name}'. "
            f"This document is structured for natural language understanding—please read and reason over the full text."
            if is_markdown
            else f"Query engine for analyzing and retrieving information from the document '{file.file_name}'. "
            f"Use this tool to perform searches and extract insights from the content of the file."
        )

        if params.query_type == "basic":
            query_engine_tools.append(
                QueryEngineTool(
                    query_engine=query_engine,
                    metadata=ToolMetadata(
                        name=f"QueryEngineTool-{file.file_name}",
                        description=description,
                    ),
                )
            )
        elif params.query_type == "text-extraction":
            query_engine_tools.append(
                QueryEngineTool.from_defaults(
                    query_engine=query_engine,
                    name=f"TextExtractionTool-{file.file_name}",
                    description=f"Extracts fields from document {file.file_name} by using the user's request.",
                )
            )

    return query_engine_tools


def create_pandas_engines_tools_from_files(files: list[ChatFile]):
    """
    Creates a list of Pandas-based function tools from a list of chat files.

    This function processes CSV and Excel files to create PandasQueryEngine instances,
    which are then wrapped into QueryEngineTool for data analysis capabilities.

    Args:
        files (List[ChatFile]): A list of ChatFile objects containing file information including
            mime_type and path_name. Only CSV and Excel files will be processed.

    Returns:
        List[QueryEngineTool]: A list of QueryEngineTool objects, each containing:
            - A pandas query engine
            - A name based on the original filename
            - A description of the tool's functionality

    Example:
        >>> chat_files = [ChatFile(mime_type="text/csv", path_name="data.csv")]
        >>> pd_tools = create_pandas_engines_tools_from_files(chat_files)
    """
    pd_tools = []
    files = [
        file
        for file in files
        if "csv" in file.mime_type.lower()
        or "excel" in file.mime_type.lower()
        or "xlsx" in file.mime_type.lower()
        or "spreadsheet" in file.mime_type.lower()
        or "sheet" in file.mime_type.lower()
        or "vnd.ms-excel" in file.mime_type.lower()
        or "vnd.openxmlformats-officedocument.spreadsheetml.sheet" in file.mime_type.lower()
    ]

    for file in files:
        if "csv" in file.mime_type.lower():
            pd_query = PandasQueryEngine(
                df=pd.read_csv(file.path_name),
                verbose=True,
            )
            tool = QueryEngineTool.from_defaults(
                query_engine=pd_query,
                name=f"PandasTool-{file.file_name}",
                description=f"Analyze, evaluate and query the CSV spreadsheet file '{file.file_name}' using Pandas.",
            )
            pd_tools.append(tool)
        if (
            "excel" in file.mime_type.lower()
            or "xlsx" in file.mime_type.lower()
            or "spreadsheet" in file.mime_type.lower()
            or "vnd.ms-excel" in file.mime_type.lower()
            or "vnd.openxmlformats-officedocument.spreadsheetml.sheet" in file.mime_type.lower()
        ):
            pd_query = PandasQueryEngine(
                df=pd.read_excel(file.path_name),
                verbose=True,
            )
            tool = QueryEngineTool.from_defaults(
                query_engine=pd_query,
                name=f"PandasTool-{file.file_name}",
                description=f"Analyze, evaluate and query the Excel spreadsheet file '{file.file_name}' using Pandas.",
            )
            pd_tools.append(tool)

    return pd_tools


def create_text_extraction_tool_from_file(query_engine: BaseQueryEngine, file: ChatFile):
    """
    Creates a text extraction tool for a given file using the specified query engine.

    This function initializes a QueryEngineTool instance configured to extract fields
    from the provided document based on the user's request. The tool is named dynamically
    using the file's name.

    Args:
        query_engine (BaseQueryEngine): The query engine used to process the document.
        file (ChatFile): The file from which fields will be extracted.

    Returns:
        QueryEngineTool: A tool configured for text extraction from the specified file.
    """
    tool = QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name=f"TextExtractionTool-{file.file_name}",
        description=f"Extracts fields from document {file.file_name} by using the user's request.",
    )
    return tool


def create_sql_engines_tools_from_files(
    files: list[ChatFile], chroma_vector_store: ChromaVectorStore
) -> list[QueryEngineTool]:
    """
    Creates a list of SQL Query Engine tools from the provided files and a Chroma vector store.

    This function processes a list of `ChatFile` objects, filters them based on metadata, and initializes
    SQL Query Engine tools for files with SQL content. It uses the provided Chroma vector store to create
    vector indices and integrates them with SQL databases to enable query execution.

    Args:
        files (List[ChatFile]): A list of `ChatFile` objects, each representing a file with metadata
            such as `id`, `mime_type`, `database_name`, and `tables`.
        chroma_vector_store (ChromaVectorStore): An instance of `ChromaVectorStore` used for creating
            vector indices and filtering based on metadata.

    Returns:
        List[QueryEngineTool]: A list of `QueryEngineTool` objects, each representing a SQL Query Engine
        tool configured for a specific database and its tables.

    Raises:
        Any exceptions raised during the initialization of vector indices, SQL databases, or query engines
        will propagate to the caller.

    Notes:
        - The function filters files based on their MIME type to identify SQL-related files.
        - It initializes a SQL database connection for each SQL file and maps its tables to a vector index.
        - The resulting tools are configured with a description and a retriever for querying the database.
    """
    storage_context = StorageContext.from_defaults(vector_store=chroma_vector_store)
    index = StrictVectorStoreIndex.from_vector_store(
        vector_store=chroma_vector_store,
        storage_context=storage_context,
        embed_model=Settings.embed_model,
    )
    sql_tools = []
    for file in files:
        filter = MetadataFilters(
            filters=[
                MetadataFilter(
                    operator=FilterOperator.EQ,
                    key="file_id",
                    value=file.id,
                )
            ]
        )

        if "sql" in file.mime_type.lower():
            pg_url = initialize_pg_url(file.database_name)
            db_engine = create_engine(pg_url)

            sql_database = SQLDatabase(db_engine, include_tables=file.tables)
            tables_node_mapping = SQLTableNodeMapping(sql_database)
            table_schema_objs = [SQLTableSchema(table_name=table_name) for table_name in file.tables]
            nodes = tables_node_mapping.to_nodes(table_schema_objs)
            for node in nodes:
                node.metadata = {
                    "file_id": file.id,
                }

            obj_index = ObjectIndex.from_objects_and_index(
                objects=table_schema_objs,
                object_mapping=tables_node_mapping,
                index=index,
            )
            query_engine = SQLTableRetrieverQueryEngine(
                sql_database=sql_database,
                table_retriever=obj_index.as_retriever(similarity_top_k=1, filter=filter),
            )
            tables_desc = ", ".join([str(x) for x in file.tables])
            desc = (
                f"SQL Query Engine for database '{file.database_name}' that can execute SQL queries on the following tables:"
                f"{tables_desc}. Use this tool when you need to query or analyze data from this database."
            )
            sql_tools.append(
                QueryEngineTool.from_defaults(
                    query_engine=query_engine,
                    name=f"SQLTool-{file.database_name}",
                    description=desc,
                )
            )
    return sql_tools


def create_url_loader_tool(chroma_vector_store: ChromaVectorStore, chat: Chat):
    """
    Creates a function tool for asynchronously scraping content from URLs.

    This function creates and returns a FunctionTool that can be used to scrape web content
    from URLs and store it in a vector index. The tool uses BeautifulSoup for web scraping
    and integrates with a ChromaVectorStore for content storage.

        chroma_vector_store (ChromaVectorStore): The vector store instance for storing scraped content.
        chat (Chat): The chat instance associated with the scraping operation.

        FunctionTool: A tool that provides URL scraping functionality with the following:
            - name: "ScrapeContentFromURL-Tool"
            - description: "Scrape from URL"
            - async function that handles the scraping operation

    Example:
        ```python
        vector_store = ChromaVectorStore()
        chat_instance = Chat()
        url_scraper_tool = create_url_loader_tool(vector_store, chat_instance)
        ```

    Notes:
        - The tool creates unique file records for each scraped URL
        - Content is stored in the provided ChromaVectorStore
        - File records are associated with the provided chat instance
    storage_context = StorageContext.from_defaults(vector_store=chroma_vector_store)
    """
    storage_context = StorageContext.from_defaults(vector_store=chroma_vector_store)

    async def async_scrape_from_url(url: str):
        """
        Asynchronously scrapes content from a given URL and stores it in a vector index.

        This function performs web scraping using BeautifulSoup, creates a file record,
        and indexes the content for future retrieval.

        Args:
            url (str): The URL to scrape content from.

        Returns:
            tuple: A tuple containing:
                - str: The original URL
                - Document: The scraped document object containing the webpage content

        Raises:
            BeautifulSoupWebReaderError: If there are issues scraping the webpage
            VectorStoreIndexError: If there are issues creating the vector index
        """
        reader = BeautifulSoupWebReader()
        documents = reader.load_data([url])

        db_file = ChatFile(
            id=str(uuid.uuid4()),
            file_name=url,
            path_name=url,
            mime_type="text/html",
            chat_id=chat.id,
            database_name=None,
            database_type=None,
            tables=None,
        )

        for document in documents:
            document.metadata = {
                "file_id": db_file.id,
            }

        StrictVectorStoreIndex.from_documents(
            documents=[documents[0]],
            storage_context=storage_context,
            show_progress=True,
        )
        chat.files.append(db_file)
        return url, documents[0]

    return FunctionTool.from_defaults(
        async_fn=async_scrape_from_url,
        name="ScrapeContentFromLinkTool",
        description="Asynchronously scrape and process website content from a given URL. "
        "The tool extracts the content, stores it in a vector index, and associates it "
        "with the current chat session for future queries.",
    )


def create_search_engine_tool(chroma_vector_store: ChromaVectorStore, chat: Chat):
    """
    Creates a search engine tool that uses DuckDuckGo to search for documents based on a user-provided query.
    The tool retrieves hyperlinks, scrapes the content of the URLs, and stores the documents in a vector store.

    Args:
        chroma_vector_store (ChromaVectorStore): The vector store used for storing document embeddings.
        chat (Chat): The chat instance to associate the retrieved documents with.

    Returns:
        FunctionTool: A tool that can be used to perform searches and store the results in the vector store.

    The tool performs the following steps:
        1. Uses DuckDuckGo to perform a search and retrieve hyperlinks.
        2. Scrapes the content of the retrieved URLs using BeautifulSoupWebReader.
        3. Creates ChatFile instances for each document and associates them with the provided chat.
        4. Stores the documents in the vector store with metadata and embeddings.
    """
    storage_context = StorageContext.from_defaults(vector_store=chroma_vector_store)
    reader = DuckDuckGoSearchToolSpec()

    def search_engine_tool(query: str):
        """
        Perform a search query using DuckDuckGo, scrape the resulting web pages, and process the content into documents.

        Args:
            query (str): The search query string.

        Returns:
            List[str]: A list of text content extracted from the scraped web pages.

        Workflow:
            1. Perform a DuckDuckGo search using the provided query and retrieve up to 3 results.
            2. Extract URLs from the search results.
            3. Scrape the content of the web pages corresponding to the URLs using BeautifulSoupWebReader.
            4. For each scraped document:
                - Create a ChatFile object to represent the document metadata.
                - Append the ChatFile object to the chat's file list.
                - Store the document in a vector store index for further processing.
            5. Return the text content of the scraped documents.
        """
        hyperlinks = reader.duckduckgo_full_search(query, max_results=3)
        urls = [hyperlink["href"] for hyperlink in hyperlinks]
        scraper = BeautifulSoupWebReader()
        documents = scraper.load_data(urls=urls)

        for i, document in enumerate(documents):
            db_file = ChatFile(
                id=str(uuid.uuid4()),
                file_name=urls[i],
                path_name=urls[i],
                database_name=None,
                database_type=None,
                chat_id=chat.id,
                tables=None,
                mime_type="text/html",
            )
            document.metadata = {
                "file_id": db_file.id,
            }
            chat.files.append(db_file)
            StrictVectorStoreIndex.from_documents(
                documents=[document],
                vector_store=chroma_vector_store,
                storage_context=storage_context,
                embed_model=Settings.embed_model,
                show_progress=True,
            )
        return [document.text for document in documents]

    return FunctionTool.from_defaults(
        fn=search_engine_tool,
        name="DuckDuckGoSearchTool",
        description="Perform a web search using DuckDuckGo based on a user-provided query. "
        "The tool retrieves top results, scrapes the content of the linked web pages, "
        "and stores the processed content in a vector index for future queries.",
    )
