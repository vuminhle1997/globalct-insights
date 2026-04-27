import os
from pathlib import Path

import yaml
from fastapi import Depends, HTTPException
from redis import Redis
from starlette.requests import Request

from backend.dependencies import get_redis_client
from backend.routers.custom_router import APIRouter

router = APIRouter(
    prefix="/models",
    tags=["models"],
    responses={404: {"description": "Not found"}},
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


def get_models_from_yaml():
    file_path = os.path.join("backend", "models.yml")
    # load in $PWD/backend/models.yaml
    with open(file_path) as f:
        models = yaml.safe_load(f)
    return models


@router.get("")
def get_models(
    request: Request,
    redis_client: Redis = Depends(get_redis_client),
):

    if not request.cookies.get("session_id"):
        raise HTTPException(status_code=404, detail="Session ID not found")

    claims = redis_client.get(f"session:{request.cookies.get('session_id')}")
    if not claims:
        raise HTTPException(status_code=404, detail="Invalid session ID")
    return get_models_from_yaml()
