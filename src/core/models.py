"""
Модели данных для поиска дубликатов.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


SearchMode = Literal["single_list", "two_lists"]
MatchType = Literal["exact", "filename"]
ListSource = Literal["list1", "list2"]


@dataclass
class SearchConfig:
    """Конфигурация поиска дубликатов."""

    mode: SearchMode
    list1_paths: list[Path]
    list2_paths: list[Path]
    include_subfolders1: bool
    include_subfolders2: bool
    match_type: MatchType
    images_only: bool


@dataclass
class FileEntry:
    """Файл, участвующий в поиске."""

    path: Path
    size: int
    hash_value: str | None = None
    source: ListSource = "list1"
    mtime: float = 0.0


@dataclass
class DuplicateGroup:
    """Группа дубликатов."""

    key: str
    files: list[FileEntry] = field(default_factory=list)
    keep_suggestion: Path | None = None

    def __post_init__(self) -> None:
        if self.files and self.keep_suggestion is None:
            oldest = min(self.files, key=lambda entry: entry.mtime)
            self.keep_suggestion = oldest.path


@dataclass
class ScanProgress:
    """Состояние прогресса сканирования."""

    phase: str = "enumerating"
    files_scanned: int = 0
    files_hashed: int = 0
    total_files: int = 0
    groups_found: int = 0
    current_path: str = ""
    status_text: str = ""
    percent: float | None = None


@dataclass
class ScanResult:
    """Результат сканирования."""

    groups: list[DuplicateGroup] = field(default_factory=list)
    total_files_scanned: int = 0
    canceled: bool = False
    search_mode: SearchMode = "single_list"

    @property
    def duplicate_file_count(self) -> int:
        return sum(max(0, len(group.files) - 1) for group in self.groups)

    @property
    def reclaimable_bytes(self) -> int:
        total = 0
        for group in self.groups:
            if group.keep_suggestion is None:
                continue
            for entry in group.files:
                if entry.path != group.keep_suggestion:
                    total += entry.size
        return total
