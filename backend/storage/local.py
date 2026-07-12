"""Local-filesystem storage backend."""

from __future__ import annotations

import os
from pathlib import Path

import structlog

from backend.core.config import settings
from backend.storage.base import StorageBackend

logger = structlog.get_logger(__name__)


class LocalStorage(StorageBackend):
    """Stores files under UPLOAD_DIR on the local filesystem."""

    def __init__(self, base_dir: str | None = None) -> None:
        """Ensure the base upload directory exists."""
        self._base = Path(base_dir or settings.UPLOAD_DIR).resolve()
        self._base.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        """Resolve a key to an absolute path, preventing traversal."""
        candidate = (self._base / key).resolve()
        if not str(candidate).startswith(str(self._base)):
            raise ValueError("Path traversal detected in storage key")
        return candidate

    async def save(self, *, key: str, data: bytes) -> str:
        """Write bytes to <base>/<key> and return the absolute path."""
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        logger.info("file_saved", path=str(target), size=len(data))
        return str(target)

    async def read(self, path: str) -> bytes:
        """Read bytes from an absolute stored path."""
        return Path(path).read_bytes()

    async def delete(self, path: str) -> bool:
        """Delete a stored file; return True if it existed."""
        p = Path(path)
        if p.exists():
            os.remove(p)
            return True
        return False


_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return a process-wide storage backend singleton."""
    global _storage
    if _storage is None:
        _storage = LocalStorage()
    return _storage
