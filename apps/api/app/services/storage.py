import aiofiles
from pathlib import Path
from typing import Protocol


class Storage(Protocol):
    async def save(self, key: str, data: bytes, content_type: str) -> str: ...
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
