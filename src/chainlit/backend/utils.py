from fastapi import HTTPException, Request

from chainlit.config import config
from chainlit.backend.base import BaseBackend
from chainlit.backend.local import LocalBackend
from chainlit.backend.cloud import CloudBackend


async def get_backend(request: Request) -> BaseBackend:
    auth_header = request.headers.get("Authorization")

    backend = config.project.backend

    if backend == "local":
        client = LocalBackend()
    elif backend == "cloud":
        client = CloudBackend(config.project.id, auth_header)
    else:
        raise HTTPException(status_code=500, detail="Invalid database type")

    return client
