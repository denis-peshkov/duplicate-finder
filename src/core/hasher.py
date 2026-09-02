"""
Хеширование файлов для поиска exact-дубликатов.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

PARTIAL_CHUNK_SIZE = 64 * 1024


def partial_hash(path: Path, cancel_check: Callable[[], bool] | None = None) -> str:
    """Быстрый partial hash: первые и последние 64 KB."""
    digest = hashlib.blake2b(digest_size=16)
    size = path.stat().st_size

    with open(path, "rb") as handle:
        head = handle.read(PARTIAL_CHUNK_SIZE)
        digest.update(head)

        if size > PARTIAL_CHUNK_SIZE:
            if cancel_check and cancel_check():
                return ""
            if size > PARTIAL_CHUNK_SIZE * 2:
                handle.seek(-PARTIAL_CHUNK_SIZE, 2)
            else:
                handle.seek(PARTIAL_CHUNK_SIZE)
            tail = handle.read(PARTIAL_CHUNK_SIZE)
            digest.update(tail)

    return digest.hexdigest()


def full_hash(path: Path, cancel_check: Callable[[], bool] | None = None) -> str:
    """Полный hash содержимого файла."""
    digest = hashlib.blake2b(digest_size=16)

    with open(path, "rb") as handle:
        while True:
            if cancel_check and cancel_check():
                return ""
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def hash_file(
    path: Path,
    cancel_check: Callable[[], bool] | None = None,
) -> str:
    """Полный hash для финального сравнения."""
    try:
        return full_hash(path, cancel_check=cancel_check)
    except OSError as exc:
        logger.warning("Не удалось хешировать %s: %s", path, exc)
        return ""
