import asyncio
import os
from pathlib import Path

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_pagination import add_pagination
from hypercorn.asyncio import serve
from hypercorn.config import Config
from llama_index.core.settings import Settings
from starlette.requests import Request
from starlette.types import ASGIApp

from backend.core.config import CHUNK_OVERLAP, CHUNK_SIZE, CORS_ORIGINS, ENV, LLM_PROVIDER, PORT
from backend.dependencies import logger
from backend.routers.api.auth import router as auth_router
from backend.routers.route import router
from backend.services.llm_factory import create_embed_model, create_llm


def check_required_env_vars():
    import sys

    required_vars = [
        "CLIENT_ID",
        "CLIENT_SECRET",
        "TENANT_ID",
        "REDIRECT_URI",
        "FRONTEND_URL",
        "ALLOWED_GROUPS_IDS",
        "REDIS_HOST",
        "REDIS_PORT",
        "DATABASE_URL",
        "PG_HOST",
        "PG_PORT",
        "PG_USER",
        "PG_PASSWORD",
        "PG_COLLECTION",
        "MYSQL_HOST",
        "MYSQL_PORT",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "CHROMA_HOST",
        "CHROMA_PORT",
        "PHOENIX_API_KEY",
        "PHOENIX_COLLECTOR_ENDPOINT",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)


def _is_endpoint_reachable(url: str, timeout: float = 1.0) -> bool:
    """Return True when an HTTP endpoint is reachable (status code is irrelevant)."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code >= 100
    except requests.RequestException:
        return False


# loads envs and setup Phoenix monitoring
try:
    phoenix_key, phoenix_url = os.getenv("PHOENIX_API_KEY"), os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
    if not phoenix_key or not phoenix_url:
        logger.info("Phoenix tracing disabled: PHOENIX_API_KEY or PHOENIX_COLLECTOR_ENDPOINT is missing")
    elif not _is_endpoint_reachable(phoenix_url):
        logger.warning(f"Phoenix tracing disabled: endpoint unreachable at {phoenix_url}")
    else:
        from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
        from phoenix.otel import register

        logger.info(f"Setting up Arize Phoenix Tracing at: {phoenix_url}")
        tracer_provider = register(
            project_name="globalct-insights", auto_instrument=True, batch=True, set_global_tracer_provider=False
        )
        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
except Exception as e:
    logger.error(f"Startup error: {e}")


base_dir = Path(__file__).resolve().parent
uploads_dir = base_dir / "uploads" / "avatars"

if not uploads_dir.exists():
    # parents=True ensures 'uploads' is created if it doesn't exist
    # exist_ok=True prevents errors if another process creates it simultaneously
    uploads_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directory: {uploads_dir}")

# Initialize LLM and embedding model based on provider
llm = create_llm(LLM_PROVIDER)
embed_model = create_embed_model(LLM_PROVIDER)

# Set global settings for LLM and embedding model
Settings.llm = llm
Settings.embed_model = embed_model
Settings.chunk_size = CHUNK_SIZE
Settings.chunk_overlap = CHUNK_OVERLAP

app = FastAPI()
app.include_router(router)
app.include_router(auth_router)
add_pagination(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Allow frontend URLs
    allow_credentials=True,  # Required for cookies/sessions
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.mount("/uploads/avatars", StaticFiles(directory="backend/uploads/avatars"), name="avatar")


# Middleware to log requests
@app.middleware("http")
async def log_requests(request: Request, call_next: ASGIApp):
    logger.info(
        f"Request: {request.method} {request.url}, \n "
        f"ip-address: {request.client.host} \n "
        f"agent: {request.headers.get('User-Agent')} \n "
        f"accept: {request.headers.get('Accept')}"
    )
    try:
        response = await call_next(request)
    except Exception as ex:
        logger.error(f"Request failed: {ex}", exc_info=True)
        raise
    return response


# @app.on_event("startup")
# def on_startup():
#     logger.debug(f"Redirect url: {REDIRECT_URI} \n FRONTEND_URL: {FRONTEND_URL}")
#     logger.debug("Creating tables for Database")
#     # NOTE: In production, use Alembic migrations instead of this.
#     # This is kept for development/testing convenience only.
#     create_db_and_tables()


if __name__ == "__main__":
    logger.debug(f"Backend running at port: {PORT}")
    config = Config()
    config.bind = [f"0.0.0.0:{PORT}"]
    asyncio.run(serve(app, config))

