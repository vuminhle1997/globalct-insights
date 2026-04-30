import os
from pathlib import Path

import yaml
from fastapi import Depends
from redis import Redis
from starlette.requests import Request

from backend.dependencies import get_redis_client
from backend.routers.custom_router import APIRouter
from backend.services.session.session_service import verify_session_exists

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

    verify_session_exists(request, redis_client)
    return get_models_from_yaml()
