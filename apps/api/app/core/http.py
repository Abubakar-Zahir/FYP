from typing import Annotated

import httpx
from fastapi import Depends, Request


def get_http_client(request: Request) -> httpx.AsyncClient:
    """One shared client per process, opened and closed by the app's lifespan."""
    client: httpx.AsyncClient = request.app.state.http
    return client


HttpClientDependency = Annotated[httpx.AsyncClient, Depends(get_http_client)]
