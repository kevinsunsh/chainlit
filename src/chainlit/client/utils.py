from fastapi import HTTPException, Request

from chainlit.config import config
from chainlit.client.base import BaseClient
from chainlit.client.local import LocalClient
from chainlit.client.cloud import CloudClient


async def get_client(request: Request) -> BaseClient:
    auth_header = request.headers.get("Authorization")

    backend = config.project.backend

    if backend == "local":
        client = LocalClient()
    elif backend == "cloud":
        client = CloudClient(config.project.id, auth_header)
    else:
        raise HTTPException(status_code=500, detail="Invalid database type")

    return client
