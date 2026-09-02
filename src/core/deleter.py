"""
Удаление файлов в корзину.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from send2trash import send2trash

logger = logging.getLogger(__name__)


@dataclass
class DeleteResult:
    """Результат удаления файлов."""

    deleted: list[Path]
    failed: list[tuple[Path, str]]


def delete_to_recycle_bin(paths: list[Path]) -> DeleteResult:
    """Переместить файлы в корзину."""
    deleted: list[Path] = []
    failed: list[tuple[Path, str]] = []

    for path in paths:
        try:
            send2trash(str(path))
            deleted.append(path)
            logger.info("Файл перемещён в корзину: %s", path)
        except Exception as exc:  # noqa: BLE001 — send2trash может бросать разные исключения
            message = str(exc)
            failed.append((path, message))
            logger.error("Не удалось удалить %s: %s", path, message)

    return DeleteResult(deleted=deleted, failed=failed)
