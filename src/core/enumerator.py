"""
Обход файлов и папок для поиска дубликатов.
"""

from __future__ import annotations

import logging
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
        return Path(text[:-1]), True
    return Path(text), False


def format_list_item(path: Path, is_folder: bool) -> str:
    """Форматирование элемента для отображения в списке."""
    if is_folder:
        return f"{path}\\*"
    return str(path)


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def enumerate_paths(
    raw_items: Iterable[str],
    include_subfolders: bool,
    images_only: bool,
    source: ListSource,
    on_file: Callable[[FileEntry], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> list[FileEntry]:
    """Собрать файлы из списка путей."""
    entries: list[FileEntry] = []

    for raw_item in raw_items:
        if cancel_check and cancel_check():
            break

        path, is_folder = parse_list_item(raw_item)
        if not path.exists():
            logger.warning("Путь не найден: %s", path)
            continue

        try:
            if path.is_file():
                if images_only and not _is_image(path):
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
                    )
                else:
                    for child in path.iterdir():
                        if cancel_check and cancel_check():
                            break
                        if child.is_file():
                            if images_only and not _is_image(child):
                                continue
                            entry = _make_entry(child, source)
                            entries.append(entry)
                            if on_file:
                                on_file(entry)
        except OSError as exc:
            logger.warning("Ошибка доступа к %s: %s", path, exc)

    return entries


def _walk_directory(
    directory: Path,
    include_subfolders: bool,
    images_only: bool,
    source: ListSource,
    entries: list[FileEntry],
    on_file: Callable[[FileEntry], None] | None,
    cancel_check: Callable[[], bool] | None,
) -> None:
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
        try:
            entry = _make_entry(item, source)
            entries.append(entry)
            if on_file:
                on_file(entry)
        except OSError as exc:
            logger.warning("Ошибка чтения %s: %s", item, exc)


def _make_entry(path: Path, source: ListSource) -> FileEntry:
    stat = path.stat()
    return FileEntry(
        path=path.resolve(),
        size=stat.st_size,
        source=source,
        mtime=stat.st_mtime,
    )
