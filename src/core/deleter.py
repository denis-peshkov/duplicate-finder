"""
Удаление файлов в корзину.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from send2trash import send2trash

logger = logging.getLogger(__name__)


@dataclass
class DeleteProgress:
    """Прогресс удаления файлов или очистки пустых папок."""

    current: int = 0
    total: int = 0
    current_path: str = ""
    canceled: bool = False
    phase: str = "files"  # files | folders
    folders_scanned: int = 0
    folders_removed: int = 0


@dataclass
class DeleteResult:
    """Результат удаления файлов."""

    deleted: list[Path]
    failed: list[tuple[Path, str]]
    canceled: bool = False
    folders_removed: list[Path] = field(default_factory=list)
    folders_failed: list[tuple[Path, str]] = field(default_factory=list)


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
                        phase="files",
                    )
                )
            return DeleteResult(deleted=deleted, failed=failed, canceled=True)

        if progress_callback:
            progress_callback(
                DeleteProgress(
                    current=index,
                    total=total,
                    current_path=str(path),
                    phase="files",
                )
            )

        try:
            send2trash(str(path))
            deleted.append(path)
            logger.info("Moved to Recycle Bin: %s", path)
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            failed.append((path, message))
            logger.error("Failed to delete %s: %s", path, message)

    return DeleteResult(deleted=deleted, failed=failed, canceled=False)


def _resolve_path(path: Path) -> Path:
    """Вернуть абсолютный путь или исходный при ошибке resolve."""
    try:
        return path.resolve()
    except OSError:
        return path


def _try_remove_empty_dir(
    folder: Path,
    removed: list[Path],
    failed: list[tuple[Path, str]],
) -> bool:
    """Удалить каталог, если пуст. Возвращает True, если удалён."""
    try:
        if not folder.is_dir():
            return False
        if any(folder.iterdir()):
            return False
    except OSError as exc:
        failed.append((folder, str(exc)))
        logger.error("Failed to read folder %s: %s", folder, exc)
        return False

    try:
        send2trash(str(folder))
        removed.append(folder)
        logger.info("Empty folder moved to Recycle Bin: %s", folder)
        return True
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        failed.append((folder, message))
        logger.error("Failed to delete empty folder %s: %s", folder, message)
        return False


def remove_empty_folders(
    roots: list[Path] | None = None,
    progress_callback: Callable[[DeleteProgress], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> tuple[list[Path], list[tuple[Path, str]]]:
    """
    Быстро обойти все указанные корни поиска и удалить пустые папки.

    Папка считается пустой, если в ней нет ни файлов, ни подпапок
    (обход снизу вверх — вложенные пустые удаляются первыми).
    Сами search roots не удаляются.
    """
    removed: list[Path] = []
    failed: list[tuple[Path, str]] = []
    root_list = list(roots or [])
    if not root_list:
        logger.warning("remove_empty_folders: no search roots, skipping")
        return removed, failed

    scanned = 0
    last_emit_at = 0.0

    def emit(folder: Path, *, force: bool = False) -> None:
        """Отправить throttled-прогресс очистки пустых папок."""
        nonlocal last_emit_at
        if not progress_callback:
            return
        now = time.monotonic()
        if not force and (now - last_emit_at) < 0.05:
            return
        last_emit_at = now
        progress_callback(
            DeleteProgress(
                phase="folders",
                folders_scanned=scanned,
                folders_removed=len(removed),
                current_path=str(folder),
                current=len(removed),
                total=0,
            )
        )

    if progress_callback:
        progress_callback(
            DeleteProgress(
                phase="folders",
                folders_scanned=0,
                folders_removed=0,
                current_path="",
            )
        )

    seen_roots: set[Path] = set()
    for root in root_list:
        if cancel_check and cancel_check():
            break

        root_path = Path(root)
        if not root_path.is_dir():
            continue

        root_res = _resolve_path(root_path)
        if root_res in seen_roots:
            continue
        seen_roots.add(root_res)

        try:
            walker = os.walk(root_res, topdown=False)
        except OSError as exc:
            failed.append((root_res, str(exc)))
            logger.error("Failed to walk %s: %s", root_res, exc)
            continue

        for dirpath, _dirnames, _filenames in walker:
            if cancel_check and cancel_check():
                emit(Path(dirpath), force=True)
                return removed, failed
            folder = Path(dirpath)
            scanned += 1
            if _resolve_path(folder) == root_res:
                emit(folder)
                continue
            was_removed = _try_remove_empty_dir(folder, removed, failed)
            emit(folder, force=was_removed)

    if progress_callback:
        progress_callback(
            DeleteProgress(
                phase="folders",
                folders_scanned=scanned,
                folders_removed=len(removed),
                current_path="",
            )
        )

    return removed, failed
