import asyncio
import aiofiles
from pathlib import Path
from typing import Protocol

import boto3
from botocore.config import Config

from app.core.config import settings


class Storage(Protocol):
    """Storage abstraction. Keys user-isolated (e.g. users/<uid>/...). Originals never deleted."""

    async def save(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str: ...
    async def get(self, key: str) -> bytes: ...


class LocalStorage:
    def __init__(self, root: str = "./storage"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, key: str) -> Path:
        # Prevent path traversal
        p = (self.root / key).resolve()
        if not str(p).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key")
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    async def save(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        p = self._safe_path(key)
        async with aiofiles.open(p, "wb") as f:
            await f.write(data)
        return str(p)

    async def get(self, key: str) -> bytes:
        p = self._safe_path(key)
        async with aiofiles.open(p, "rb") as f:
            return await f.read()


class S3Storage:
    """S3-compatible backend (MinIO dev parity, real S3 prod).
    Same contract as local. Keys are object keys (user-isolated paths).
    Originals preserved; no delete on this path.
    """

    def __init__(self) -> None:
        if not settings.S3_BUCKET:
            raise RuntimeError("STORAGE_BACKEND=s3 requires S3_BUCKET in config")
        self.bucket = settings.S3_BUCKET
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION or "us-east-1",
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},  # MinIO + many compat setups
            ),
        )

    async def save(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        def _put() -> str:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return f"s3://{self.bucket}/{key}"

        return await asyncio.to_thread(_put)

    async def get(self, key: str) -> bytes:
        def _get() -> bytes:
            resp = self.s3.get_object(Bucket=self.bucket, Key=key)
            return resp["Body"].read()

        return await asyncio.to_thread(_get)


def get_storage() -> Storage:
    """Factory per settings. Default local (Win/Docker friendly named volumes)."""
    if settings.STORAGE_BACKEND == "s3":
        return S3Storage()
    return LocalStorage(root=settings.STORAGE_LOCAL_ROOT)
