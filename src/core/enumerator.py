"""
Обход файлов и папок для поиска дубликатов.
"""

from __future__ import annotations

import fnmatch
import logging
import os
from pathlib import Path
from typing import Callable, Iterable

from src.core.models import FileEntry, ListSource

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff",
    ".heic",
}


def parse_list_item(raw_path: str) -> tuple[Path, bool]:
    """Разбор элемента списка: файл или папка с суффиксом *."""
    text = raw_path.strip()
    if text.endswith("*"):
        # folder\* / folder/* — убрать маркер и разделитель перед ним
        text = text[:-1].rstrip("\\/")
        return Path(text), True
    return Path(text), False


def format_list_item(path: Path, is_folder: bool) -> str:
    """Форматирование элемента для отображения в списке."""
    if is_folder:
        return f"{path}{os.sep}*"
    return str(path)


def _is_image(path: Path) -> bool:
    """Проверить, что расширение файла относится к изображениям."""
    return path.suffix.lower() in IMAGE_EXTENSIONS


def matches_mask(path: Path, masks: Iterable[str]) -> bool:
    """Проверка пути/имени файла по маскам (fnmatch)."""
    name = path.name
    full = str(path)
    full_fwd = full.replace("\\", "/")
    for raw in masks:
        mask = raw.strip()
        if not mask:
            continue
        mask_fwd = mask.replace("\\", "/")
        if fnmatch.fnmatch(name, mask) or fnmatch.fnmatch(full, mask):
            return True
        if fnmatch.fnmatch(full_fwd, mask_fwd) or fnmatch.fnmatch(name, mask_fwd):
            return True
    return False


def matches_exclude_mask(path: Path, masks: Iterable[str]) -> bool:
    """Совместимость: то же, что matches_mask."""
    return matches_mask(path, masks)


def _normalize_masks(masks: Iterable[str] | None) -> list[str]:
    """Нормализовать список масок: trim и отбросить пустые."""
    return [mask.strip() for mask in (masks or []) if mask and mask.strip()]


def should_keep_file(
    path: Path,
    include_masks: Iterable[str] | None,
    exclude_masks: Iterable[str] | None,
) -> bool:
    """
    Include: пустой список — все файлы; иначе нужен матч хотя бы одной маски.
    Exclude: матч любой маски — файл отбрасывается.
    """
    includes = _normalize_masks(include_masks)
    excludes = _normalize_masks(exclude_masks)
    if includes and not matches_mask(path, includes):
        return False
    if excludes and matches_mask(path, excludes):
        return False
    return True


def enumerate_paths(
    raw_items: Iterable[str],
    include_subfolders: bool,
    images_only: bool,
    source: ListSource,
    on_file: Callable[[FileEntry], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
    exclude_masks: Iterable[str] | None = None,
    include_masks: Iterable[str] | None = None,
) -> list[FileEntry]:
    """Собрать файлы из списка путей."""
    entries: list[FileEntry] = []
    includes = _normalize_masks(include_masks)
    excludes = _normalize_masks(exclude_masks)

    for raw_item in raw_items:
        if cancel_check and cancel_check():
            break

        path, is_folder = parse_list_item(raw_item)
        if not path.exists():
            logger.warning("Path not found: %s", path)
            continue

        try:
            if path.is_file():
                if images_only and not _is_image(path):
                    continue
                if not should_keep_file(path, includes, excludes):
                    continue
                entry = _make_entry(path, source)
                entries.append(entry)
                if on_file:
                    on_file(entry)
            elif path.is_dir():
                if is_folder or include_subfolders:
                    _walk_directory(
                        path,
                        include_subfolders,
                        images_only,
                        source,
                        entries,
                        on_file,
                        cancel_check,
                        includes,
                        excludes,
                    )
                else:
                    for child in path.iterdir():
                        if cancel_check and cancel_check():
                            break
                        if child.is_file():
                            if images_only and not _is_image(child):
                                continue
                            if not should_keep_file(child, includes, excludes):
                                continue
                            entry = _make_entry(child, source)
                            entries.append(entry)
                            if on_file:
                                on_file(entry)
        except OSError as exc:
            logger.warning("Access error for %s: %s", path, exc)

    return entries


def _walk_directory(
    directory: Path,
    include_subfolders: bool,
    images_only: bool,
    source: ListSource,
    entries: list[FileEntry],
    on_file: Callable[[FileEntry], None] | None,
    cancel_check: Callable[[], bool] | None,
    include_masks: list[str],
    exclude_masks: list[str],
) -> None:
    """Обойти каталог и добавить подходящие файлы в entries."""
    if include_subfolders:
        iterator = directory.rglob("*")
    else:
        iterator = directory.iterdir()

    for item in iterator:
        if cancel_check and cancel_check():
            break
        if not item.is_file():
            continue
        if images_only and not _is_image(item):
            continue
        if not should_keep_file(item, include_masks, exclude_masks):
            continue
        try:
            entry = _make_entry(item, source)
            entries.append(entry)
            if on_file:
                on_file(entry)
        except OSError as exc:
            logger.warning("Read error for %s: %s", item, exc)


def _make_entry(path: Path, source: ListSource) -> FileEntry:
    """Создать FileEntry по пути и источнику списка."""
    stat = path.stat()
    return FileEntry(
        path=path.resolve(),
        size=stat.st_size,
        source=source,
        mtime=stat.st_mtime,
    )
