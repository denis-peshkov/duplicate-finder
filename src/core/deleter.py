"""
Удаление файлов в корзину.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from send2trash import send2trash

logger = logging.getLogger(__name__)


@dataclass
class DeleteProgress:
    """Прогресс удаления."""

    current: int
    total: int
    current_path: str = ""
    canceled: bool = False


@dataclass
class DeleteResult:
    """Результат удаления файлов."""

    deleted: list[Path]
    failed: list[tuple[Path, str]]
    canceled: bool = False


def delete_to_recycle_bin(
    paths: list[Path],
    progress_callback: Callable[[DeleteProgress], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> DeleteResult:
    """Переместить файлы в корзину с опциональным прогрессом."""
    deleted: list[Path] = []
    failed: list[tuple[Path, str]] = []
    total = len(paths)

    for index, path in enumerate(paths, start=1):
        if cancel_check and cancel_check():
            if progress_callback:
                progress_callback(
                    DeleteProgress(
                        current=index - 1,
                        total=total,
                        current_path=str(path),
                        canceled=True,
                    )
                )
            return DeleteResult(deleted=deleted, failed=failed, canceled=True)

        if progress_callback:
            progress_callback(
                DeleteProgress(
                    current=index,
                    total=total,
                    current_path=str(path),
                )
            )

        try:
            send2trash(str(path))
            deleted.append(path)
            logger.info("Файл перемещён в корзину: %s", path)
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            failed.append((path, message))
            logger.error("Не удалось удалить %s: %s", path, message)

    return DeleteResult(deleted=deleted, failed=failed, canceled=False)
