"""Abstract storage backend for uploaded files."""

from __future__ import annotations

import abc


class StorageBackend(abc.ABC):
    """Persists raw uploaded file bytes and returns a retrievable path."""

    @abc.abstractmethod
    async def save(self, *, key: str, data: bytes) -> str:
        """Persist bytes under a key and return the stored path/URI."""

    @abc.abstractmethod
    async def read(self, path: str) -> bytes:
        """Read previously stored bytes by path."""

    @abc.abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete a stored file; return True if it existed."""
