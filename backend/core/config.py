import os

from dotenv import load_dotenv

load_dotenv()

# Azure AD
CLIENT_ID: str = os.getenv("CLIENT_ID", "")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")
TENANT_ID: str = os.getenv("TENANT_ID", "")
AUTHORITY: str = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES: list[str] = ["User.Read"]
REDIRECT_URI: str = os.getenv("REDIRECT_URI", "http://localhost:4000/redirect")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
ALLOWED_GROUPS_IDS: list[str] = [g for g in os.getenv("ALLOWED_GROUPS_IDS", "").split(",") if g]

# App
PORT: int = int(os.getenv("PORT", "4000"))
ENV: str = os.getenv("ENV", "development")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "OLLAMA")

# CORS origins
_CORS_DEV_ORIGINS: list[str] = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:4000",
    "http://localhost:5173",
]
CORS_ORIGINS: list[str] = (
    [FRONTEND_URL] if ENV == "production" else list({*_CORS_DEV_ORIGINS, FRONTEND_URL})
)

# Database
PG_HOST: str = os.getenv("PG_HOST", "localhost")
PG_PORT: str = os.getenv("PG_PORT", "5432")
PG_USER: str = os.getenv("PG_USER", "postgres")
PG_PASSWORD: str = os.getenv("PG_PASSWORD", "password")
PG_COLLECTION: str = os.getenv("PG_COLLECTION", "llama-rag")
DATABASE_URL: str = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_COLLECTION}"

# Redis
REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

# Chroma
CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION_NAME", "llama-rag")

# LLM settings
CHUNK_SIZE: int = 512
CHUNK_OVERLAP: int = 20
