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
    async def delete_prefix(self, prefix: str) -> int: ...


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

    async def delete_prefix(self, prefix: str) -> int:
        root = self.root.resolve()
        target = (self.root / prefix).resolve()
        if not str(target).startswith(str(root)):
            raise ValueError("Invalid storage prefix")
        if not target.exists():
            return 0
        deleted = 0
        for path in sorted(target.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
                deleted += 1
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
        try:
            target.rmdir()
        except OSError:
            pass
        return deleted


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

    async def delete_prefix(self, prefix: str) -> int:
        def _delete() -> int:
            deleted = 0
            continuation = None
            while True:
                kwargs = {"Bucket": self.bucket, "Prefix": prefix}
                if continuation:
                    kwargs["ContinuationToken"] = continuation
                resp = self.s3.list_objects_v2(**kwargs)
                objects = [{"Key": item["Key"]} for item in resp.get("Contents", [])]
                if objects:
                    self.s3.delete_objects(
                        Bucket=self.bucket,
                        Delete={"Objects": objects, "Quiet": True},
                    )
                    deleted += len(objects)
                if not resp.get("IsTruncated"):
                    break
                continuation = resp.get("NextContinuationToken")
            return deleted

        return await asyncio.to_thread(_delete)


def get_storage() -> Storage:
    """Factory per settings. Default local (Win/Docker friendly named volumes)."""
    if settings.STORAGE_BACKEND == "s3":
        return S3Storage()
    return LocalStorage(root=settings.STORAGE_LOCAL_ROOT)
