"""
Удаление файлов в корзину.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
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


def _resolve_path(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path


def _try_remove_empty_dir(
    folder: Path,
    removed: list[Path],
    failed: list[tuple[Path, str]],
) -> None:
    """Удалить каталог, если в нём нет файлов и подпапок."""
    try:
        if not folder.is_dir():
            return
        if any(folder.iterdir()):
            return
    except OSError as exc:
        failed.append((folder, str(exc)))
        logger.error("Не удалось прочитать папку %s: %s", folder, exc)
        return

    try:
        send2trash(str(folder))
        removed.append(folder)
        logger.info("Пустая папка перемещена в корзину: %s", folder)
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        failed.append((folder, message))
        logger.error("Не удалось удалить пустую папку %s: %s", folder, message)


def remove_empty_folders(
    roots: list[Path] | None = None,
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
        logger.warning("remove_empty_folders: search roots не заданы, пропуск")
        return removed, failed

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
            logger.error("Не удалось обойти %s: %s", root_res, exc)
            continue

        for dirpath, _dirnames, _filenames in walker:
            if cancel_check and cancel_check():
                return removed, failed
            folder = Path(dirpath)
            if _resolve_path(folder) == root_res:
                continue
            _try_remove_empty_dir(folder, removed, failed)

    return removed, failed
