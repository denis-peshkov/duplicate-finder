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


def _folder_contains_no_files(folder: Path) -> bool:
    """True, если каталог существует и нигде внутри нет файлов."""
    try:
        if not folder.is_dir():
            return False
        for _root, _dirs, files in os.walk(folder):
            if files:
                return False
        return True
    except OSError:
        return False


def _resolve_path(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path


def _is_strictly_under_roots(folder: Path, roots: list[Path]) -> bool:
    """Папка строго внутри одного из search roots (сам root не удаляем)."""
    folder_res = _resolve_path(folder)
    for root in roots:
        root_res = _resolve_path(root)
        if folder_res == root_res:
            return False
        try:
            folder_res.relative_to(root_res)
            return True
        except ValueError:
            continue
    return False


def remove_empty_folders(
    deleted_files: list[Path],
    roots: list[Path] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> tuple[list[Path], list[tuple[Path, str]]]:
    """
    Удалить пустые папки в иерархии удалённых файлов (target-локации).

    Папка считается пустой, если в ней нет ни одного файла
    (вложенные пустые каталоги удаляются вместе с ней).

    Удаляются только папки строго внутри search roots — сами roots
    и всё выше них не трогаем.
    """
    removed: list[Path] = []
    failed: list[tuple[Path, str]] = []
    root_list = list(roots or [])
    if not root_list:
        logger.warning("remove_empty_folders: search roots не заданы, пропуск")
        return removed, failed

    ancestors: set[Path] = set()
    for path in deleted_files:
        current = path.parent
        while current.parent != current:
            if root_list and not _is_strictly_under_roots(current, root_list):
                break
            ancestors.add(current)
            current = current.parent

    for folder in sorted(ancestors, key=lambda path: len(path.parts), reverse=True):
        if cancel_check and cancel_check():
            break
        if not folder.exists():
            continue
        if root_list and not _is_strictly_under_roots(folder, root_list):
            continue
        if not _folder_contains_no_files(folder):
            continue
        try:
            send2trash(str(folder))
            removed.append(folder)
            logger.info("Пустая папка перемещена в корзину: %s", folder)
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            failed.append((folder, message))
            logger.error("Не удалось удалить пустую папку %s: %s", folder, message)

    return removed, failed
