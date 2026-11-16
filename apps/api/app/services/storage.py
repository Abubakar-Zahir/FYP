"""Video storage on Cloudflare R2 through its S3-compatible API (CLAUDE.md stack).

The browser uploads straight to R2 with a presigned URL, so video never passes through the
API. Presigning is local computation. Calls that reach R2 run off the event loop, because
boto3 is synchronous (rules.md 3.5).
"""

import asyncio
from pathlib import Path
from typing import Annotated, Any, Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import Depends, Request, status

from app.core.errors import ApiError
from app.core.settings import Settings

UPLOAD_URL_TTL_S = 15 * 60
DOWNLOAD_URL_TTL_S = 60 * 60
# R2 accepts up to 1,000 keys per delete request, like S3.
DELETE_BATCH_SIZE = 1000


class Storage(Protocol):
    def upload_url(self, key: str, content_type: str, size_bytes: int) -> str: ...

    def download_url(self, key: str) -> str: ...

    async def size_of(self, key: str) -> int | None: ...

    async def download_to(self, key: str, path: Path) -> None: ...

    async def upload_file(self, path: Path, key: str, content_type: str) -> None: ...

    async def delete(self, keys: list[str]) -> None: ...


class R2Storage:
    def __init__(self, account_id: str, access_key: str, secret_key: str, bucket: str) -> None:
        self._bucket = bucket
        # Any: boto3 builds clients at runtime and ships no type information.
        self._client: Any = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    def upload_url(self, key: str, content_type: str, size_bytes: int) -> str:
        """Signed for this exact type and size, so the URL can't be reused for a bigger file."""
        url: str = self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
                "ContentType": content_type,
                "ContentLength": size_bytes,
            },
            ExpiresIn=UPLOAD_URL_TTL_S,
        )
        return url

    def download_url(self, key: str) -> str:
        url: str = self._client.generate_presigned_url(
            "get_object", Params={"Bucket": self._bucket, "Key": key}, ExpiresIn=DOWNLOAD_URL_TTL_S
        )
        return url

    async def size_of(self, key: str) -> int | None:
        try:
            head = await asyncio.to_thread(self._client.head_object, Bucket=self._bucket, Key=key)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise
        return int(head["ContentLength"])

    async def download_to(self, key: str, path: Path) -> None:
        await asyncio.to_thread(self._client.download_file, self._bucket, key, str(path))

    async def upload_file(self, path: Path, key: str, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.upload_file, str(path), self._bucket, key, ExtraArgs={"ContentType": content_type}
        )

    async def delete(self, keys: list[str]) -> None:
        for start in range(0, len(keys), DELETE_BATCH_SIZE):
            batch = [{"Key": key} for key in keys[start : start + DELETE_BATCH_SIZE]]
            await asyncio.to_thread(
                self._client.delete_objects, Bucket=self._bucket, Delete={"Objects": batch, "Quiet": True}
            )


def build_storage(settings: Settings) -> Storage | None:
    if not (
        settings.r2_account_id and settings.r2_access_key and settings.r2_secret_key and settings.r2_bucket
    ):
        return None
    return R2Storage(
        settings.r2_account_id,
        settings.r2_access_key,
        settings.r2_secret_key.get_secret_value(),
        settings.r2_bucket,
    )


def storage_not_configured() -> ApiError:
    return ApiError(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "storage_not_configured",
        "Video storage is not configured on this server.",
    )


def get_storage(request: Request) -> Storage:
    storage: Storage | None = request.app.state.storage
    if storage is None:
        raise storage_not_configured()
    return storage


def get_optional_storage(request: Request) -> Storage | None:
    storage: Storage | None = request.app.state.storage
    return storage


StorageDependency = Annotated[Storage, Depends(get_storage)]
OptionalStorageDependency = Annotated[Storage | None, Depends(get_optional_storage)]
