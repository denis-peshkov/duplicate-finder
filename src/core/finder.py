"""
Поиск дубликатов по конфигурации.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable

from src.core.enumerator import enumerate_paths
from src.core.hasher import hash_file, partial_hash
from src.core.models import DuplicateGroup, FileEntry, ScanProgress, ScanResult, SearchConfig
from src.utils.formatters import format_count

logger = logging.getLogger(__name__)


class DuplicateFinder:
    """Поиск дубликатов файлов."""

    def __init__(
        self,
        config: SearchConfig,
        progress_callback: Callable[[ScanProgress], None] | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ):
        self.config = config
        self.progress_callback = progress_callback
        self.cancel_check = cancel_check
        self._progress = ScanProgress()
        self._last_emit_at = 0.0

    def scan(self) -> ScanResult:
        """Запуск полного сканирования."""
        if self.config.match_type == "exact":
            return self._scan_exact()
        return self._scan_filename()

    def _make_result(
        self,
        *,
        groups: list[DuplicateGroup] | None = None,
        total_files_scanned: int = 0,
        canceled: bool = False,
    ) -> ScanResult:
        return ScanResult(
            groups=groups or [],
            total_files_scanned=total_files_scanned,
            canceled=canceled,
            search_mode=self.config.mode,
        )

    def _is_canceled(self) -> bool:
        return bool(self.cancel_check and self.cancel_check())

    def _emit(self, *, force: bool = False, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self._progress, key, value)

        now = time.monotonic()
        if not force and (now - self._last_emit_at) < 0.12:
            return
        self._last_emit_at = now
        if self.progress_callback:
            # передаём снимок, чтобы UI не видел гонки
            snapshot = ScanProgress(
                phase=self._progress.phase,
                files_scanned=self._progress.files_scanned,
                files_hashed=self._progress.files_hashed,
                total_files=self._progress.total_files,
                groups_found=self._progress.groups_found,
                current_path=self._progress.current_path,
                status_text=self._progress.status_text,
                percent=self._progress.percent,
            )
            self.progress_callback(snapshot)

    def _collect_list(
        self,
        raw_items: list[str],
        include_subfolders: bool,
        source: str,
        list_label: str,
    ) -> list[FileEntry]:
        self._emit(
            force=True,
            phase="enumerating",
            current_path="",
            status_text=f"Scanning {list_label}...",
            percent=None,
        )

        def on_file(entry: FileEntry) -> None:
            self._progress.files_scanned += 1
            self._emit(
                current_path=str(entry.path),
                files_scanned=self._progress.files_scanned,
                status_text=f"{list_label}: {format_count(self._progress.files_scanned)} files found",
            )

        entries = enumerate_paths(
            raw_items,
            include_subfolders=include_subfolders,
            images_only=self.config.images_only,
            source=source,  # type: ignore[arg-type]
            on_file=on_file,
            cancel_check=self.cancel_check,
        )
        self._emit(
            force=True,
            files_scanned=self._progress.files_scanned,
            status_text=f"{list_label}: collected {format_count(len(entries))} files",
        )
        return entries

    def _scan_filename(self) -> ScanResult:
        list1 = self._collect_list(
            [str(path) for path in self.config.list1_paths],
            self.config.include_subfolders1,
            "list1",
            "File List 1",
        )
        if self._is_canceled():
            return self._make_result(total_files_scanned=len(list1), canceled=True)

        if self.config.mode == "single_list":
            self._emit(force=True, phase="matching", status_text="Matching by filename...")
            groups = self._group_by_filename(list1, min_count=2)
            return self._make_result(groups=groups, total_files_scanned=len(list1))

        list2 = self._collect_list(
            [str(path) for path in self.config.list2_paths],
            self.config.include_subfolders2,
            "list2",
            "File List 2",
        )
        if self._is_canceled():
            return self._make_result(
                total_files_scanned=len(list1) + len(list2),
                canceled=True,
            )

        self._emit(force=True, phase="matching", status_text="Matching between lists...")
        groups = self._match_filename_two_lists(list1, list2)
        return self._make_result(groups=groups, total_files_scanned=len(list1) + len(list2))

    def _group_by_filename(
        self,
        entries: list[FileEntry],
        min_count: int,
    ) -> list[DuplicateGroup]:
        buckets: dict[str, list[FileEntry]] = defaultdict(list)
        for entry in entries:
            if self._is_canceled():
                break
            buckets[entry.path.name.lower()].append(entry)

        groups: list[DuplicateGroup] = []
        for key, files in buckets.items():
            if len(files) >= min_count:
                groups.append(DuplicateGroup(key=key, files=files))
        self._emit(force=True, phase="done", groups_found=len(groups), status_text="Done")
        return groups

    def _match_filename_two_lists(
        self,
        list1: list[FileEntry],
        list2: list[FileEntry],
    ) -> list[DuplicateGroup]:
        names_in_list2: dict[str, list[FileEntry]] = defaultdict(list)
        for entry in list2:
            names_in_list2[entry.path.name.lower()].append(entry)

        groups: list[DuplicateGroup] = []
        for index, entry in enumerate(list1, start=1):
            if self._is_canceled():
                break
            key = entry.path.name.lower()
            matches = names_in_list2.get(key, [])
            if matches:
                files = [entry, *matches]
                groups.append(DuplicateGroup(key=key, files=files))
            if index % 200 == 0:
                self._emit(
                    groups_found=len(groups),
                    status_text=f"Matching filenames... {format_count(index)}/{format_count(len(list1))}",
                    percent=index / max(len(list1), 1),
                )

        self._emit(force=True, phase="done", groups_found=len(groups), status_text="Done")
        return groups

    def _scan_exact(self) -> ScanResult:
        list1 = self._collect_list(
            [str(path) for path in self.config.list1_paths],
            self.config.include_subfolders1,
            "list1",
            "File List 1",
        )
        if self._is_canceled():
            return self._make_result(total_files_scanned=len(list1), canceled=True)

        list2: list[FileEntry] = []
        if self.config.mode == "two_lists":
            list2 = self._collect_list(
                [str(path) for path in self.config.list2_paths],
                self.config.include_subfolders2,
                "list2",
                "File List 2",
            )
            if self._is_canceled():
                return self._make_result(
                    total_files_scanned=len(list1) + len(list2),
                    canceled=True,
                )

        all_entries = list1 if self.config.mode == "single_list" else list1 + list2
        hashed_entries = self._hash_entries(all_entries)
        if self._is_canceled():
            return self._make_result(
                total_files_scanned=len(all_entries),
                canceled=True,
            )

        self._emit(force=True, phase="matching", status_text="Building duplicate groups...")
        if self.config.mode == "single_list":
            groups = self._group_by_hash(hashed_entries, min_count=2)
        else:
            groups = self._match_hash_two_lists(
                [entry for entry in hashed_entries if entry.source == "list1"],
                [entry for entry in hashed_entries if entry.source == "list2"],
            )

        return self._make_result(groups=groups, total_files_scanned=len(all_entries))

    def _hash_entries(self, entries: list[FileEntry]) -> list[FileEntry]:
        by_size: dict[int, list[FileEntry]] = defaultdict(list)
        for entry in entries:
            by_size[entry.size].append(entry)

        candidates: list[FileEntry] = []
        for size_group in by_size.values():
            if len(size_group) > 1:
                candidates.extend(size_group)

        # В single-list хешируем только кандидатов; в two-lists — все (нужны пересечения)
        if self.config.mode == "two_lists":
            work_list = list(entries)
        else:
            work_list = candidates

        self._emit(
            force=True,
            phase="hashing",
            total_files=len(work_list),
            files_hashed=0,
            status_text=f"Hashing {format_count(len(work_list))} files...",
            percent=0.0,
        )

        if self.config.mode == "single_list":
            return self._hash_candidates_pipeline(candidates)

        hashed: list[FileEntry] = []
        for index, entry in enumerate(work_list, start=1):
            if self._is_canceled():
                break
            digest = hash_file(entry.path, cancel_check=self.cancel_check)
            if not digest:
                continue
            entry.hash_value = digest
            hashed.append(entry)
            self._progress.files_hashed = index
            self._emit(
                files_hashed=index,
                total_files=len(work_list),
                current_path=str(entry.path),
                status_text=(
                    f"Hashing files: {format_count(index)} / "
                    f"{format_count(len(work_list))}"
                ),
                percent=index / max(len(work_list), 1),
            )
        return hashed

    def _hash_candidates_pipeline(self, candidates: list[FileEntry]) -> list[FileEntry]:
        partial_buckets: dict[str, list[FileEntry]] = defaultdict(list)
        total = max(len(candidates), 1)

        for index, entry in enumerate(candidates, start=1):
            if self._is_canceled():
                break
            partial = partial_hash(entry.path, cancel_check=self.cancel_check)
            if not partial:
                continue
            partial_buckets[partial].append(entry)
            self._progress.files_hashed = index
            self._emit(
                files_hashed=index,
                total_files=total,
                current_path=str(entry.path),
                status_text=(
                    f"Quick hash: {format_count(index)} / {format_count(total)}"
                ),
                percent=0.5 * index / total,
            )

        full_candidates: list[FileEntry] = []
        for bucket in partial_buckets.values():
            if len(bucket) > 1:
                full_candidates.extend(bucket)

        hashed: list[FileEntry] = []
        full_total = max(len(full_candidates), 1)
        for index, entry in enumerate(full_candidates, start=1):
            if self._is_canceled():
                break
            digest = hash_file(entry.path, cancel_check=self.cancel_check)
            if not digest:
                continue
            entry.hash_value = digest
            hashed.append(entry)
            self._emit(
                files_hashed=index,
                total_files=full_total,
                current_path=str(entry.path),
                status_text=(
                    f"Full hash: {format_count(index)} / {format_count(full_total)}"
                ),
                percent=0.5 + 0.5 * index / full_total,
            )
        return hashed

    def _group_by_hash(
        self,
        entries: list[FileEntry],
        min_count: int,
    ) -> list[DuplicateGroup]:
        buckets: dict[str, list[FileEntry]] = defaultdict(list)
        for entry in entries:
            if entry.hash_value:
                buckets[entry.hash_value].append(entry)

        groups: list[DuplicateGroup] = []
        for key, files in buckets.items():
            if len(files) >= min_count:
                groups.append(DuplicateGroup(key=key, files=files))
        self._emit(force=True, phase="done", groups_found=len(groups), status_text="Done")
        return groups

    def _match_hash_two_lists(
        self,
        list1: list[FileEntry],
        list2: list[FileEntry],
    ) -> list[DuplicateGroup]:
        hashes_in_list2: dict[str, list[FileEntry]] = defaultdict(list)
        for entry in list2:
            if entry.hash_value:
                hashes_in_list2[entry.hash_value].append(entry)

        groups: list[DuplicateGroup] = []
        for entry in list1:
            if self._is_canceled():
                break
            if not entry.hash_value:
                continue
            matches = hashes_in_list2.get(entry.hash_value, [])
            if matches:
                files = [entry, *matches]
                groups.append(DuplicateGroup(key=entry.hash_value, files=files))

        self._emit(force=True, phase="done", groups_found=len(groups), status_text="Done")
        return groups
