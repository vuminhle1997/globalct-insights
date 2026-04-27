import os
from typing import Annotated

# chroma
import chromadb
from dotenv import load_dotenv
from fastapi import Depends
from llama_index.vector_stores.chroma import ChromaVectorStore
from redis import Redis
from sqlmodel import Session, SQLModel, create_engine

from backend.logging_config import setup_logging

load_dotenv()

# Logger
logger = setup_logging()

# redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

# main DB
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", 5432)
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "password")
PG_COLLECTION = os.getenv("PG_COLLECTION", "llama-rag")

DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_COLLECTION}"
engine = create_engine(DATABASE_URL)

# ollama
base_url = f"{os.getenv('OLLAMA_HOST', 'localhost')}:{os.getenv('OLLAMA_PORT', 11434)}"

# chroma DB
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION_NAME", "llama-rag")
logger.info(f"Attempting to connect to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
try:
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    chroma_client.heartbeat()  # Check connection
    logger.info("Successfully connected to ChromaDB.")
except Exception as e:
    logger.error(f"Failed to connect to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}: {e}")
    chroma_client = None


def create_db_and_tables():
    """
    Create all database tables defined in the SQLModel metadata.
    DEPRECATED: Use Alembic migrations instead. This function is kept for backward compatibility
    in development environments only. For production, run: alembic upgrade head
    """
    SQLModel.metadata.create_all(engine)


def get_db_session():
    """
    Provide a SQLModel database session.
    This function is a generator that yields a session and ensures it is closed after use.
    """
    with Session(engine) as session:
        yield session


def get_redis_client():
    """
    Provide a Redis client connection.
    This function is a generator that yields a Redis client and ensures it is closed after use.
    """
    redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    try:
        yield redis
    finally:
        redis.close()


def get_chroma_vector():
    """
    Provide a ChromaVectorStore instance for vector storage operations.
    This function is a generator that yields the vector store.
    """
    chroma_collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)
    chroma_vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    yield chroma_vector_store


def get_chroma_collection():
    """
    Provide a Chroma collection instance.
    This function is a generator that yields the Chroma collection.
    """
    chroma_collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)
    yield chroma_collection


SessionDep = Annotated[Session, Depends(get_db_session)]
