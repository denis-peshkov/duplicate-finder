"""Тесты finder."""

from __future__ import annotations

from pathlib import Path

from src.core.enumerator import format_list_item
from src.core.finder import DuplicateFinder
from src.core.models import SearchConfig


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_exact_duplicate_single_list(tmp_path: Path) -> None:
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    file1 = dir_a / "one.bin"
    file2 = dir_b / "two.bin"
    _write(file1, b"same-content")
    _write(file2, b"same-content")
    _write(dir_a / "unique.bin", b"other")

    config = SearchConfig(
        mode="single_list",
        list1_paths=[tmp_path],
        list2_paths=[],
        include_subfolders1=True,
        include_subfolders2=True,
        match_type="exact",
        images_only=False,
    )
    result = DuplicateFinder(config).scan()
    assert not result.canceled
    assert len(result.groups) == 1
    assert len(result.groups[0].files) == 2


def test_filename_duplicate_single_list(tmp_path: Path) -> None:
    _write(tmp_path / "dir1" / "photo.jpg", b"a")
    _write(tmp_path / "dir2" / "photo.jpg", b"b")

    config = SearchConfig(
        mode="single_list",
        list1_paths=[tmp_path],
        list2_paths=[],
        include_subfolders1=True,
        include_subfolders2=True,
        match_type="filename",
        images_only=False,
    )
    result = DuplicateFinder(config).scan()
    assert len(result.groups) == 1
    assert len(result.groups[0].files) == 2


def test_exact_two_lists(tmp_path: Path) -> None:
    list1 = tmp_path / "list1"
    list2 = tmp_path / "list2"
    _write(list1 / "a.bin", b"duplicate")
    _write(list2 / "b.bin", b"duplicate")
    _write(list1 / "solo.bin", b"solo")

    config = SearchConfig(
        mode="two_lists",
        list1_paths=[list1],
        list2_paths=[list2],
        include_subfolders1=True,
        include_subfolders2=True,
        match_type="exact",
        images_only=False,
    )
    result = DuplicateFinder(config).scan()
    assert len(result.groups) == 1
    sources = {entry.source for entry in result.groups[0].files}
    assert sources == {"list1", "list2"}


def test_exact_two_lists_skips_unique_sizes(tmp_path: Path) -> None:
    """Файлы уникального размера между списками не должны давать ложных групп."""
    list1 = tmp_path / "list1"
    list2 = tmp_path / "list2"
    _write(list1 / "big.bin", b"x" * 100)
    _write(list2 / "small.bin", b"y" * 10)
    _write(list1 / "same.bin", b"z" * 20)
    _write(list2 / "same2.bin", b"z" * 20)

    config = SearchConfig(
        mode="two_lists",
        list1_paths=[list1],
        list2_paths=[list2],
        include_subfolders1=True,
        include_subfolders2=True,
        match_type="exact",
        images_only=False,
    )
    result = DuplicateFinder(config).scan()
    assert len(result.groups) == 1
    names = {entry.path.name for entry in result.groups[0].files}
    assert names == {"same.bin", "same2.bin"}


def test_filename_two_lists(tmp_path: Path) -> None:
    list1 = tmp_path / "list1"
    list2 = tmp_path / "list2"
    _write(list1 / "match.txt", b"1")
    _write(list2 / "match.txt", b"2")
    _write(list1 / "other.txt", b"3")

    config = SearchConfig(
        mode="two_lists",
        list1_paths=[list1],
        list2_paths=[list2],
        include_subfolders1=True,
        include_subfolders2=True,
        match_type="filename",
        images_only=False,
    )
    result = DuplicateFinder(config).scan()
    assert len(result.groups) == 1
    assert result.groups[0].key == "match.txt"


def test_exact_respects_include_and_exclude_masks(tmp_path: Path) -> None:
    root = tmp_path / "root"
    _write(root / "keep.bin", b"same")
    _write(root / "also.bin", b"same")
    _write(root / "skip.tmp", b"same")
    _write(root / "other.txt", b"same")

    config = SearchConfig(
        mode="single_list",
        list1_paths=[root],
        list2_paths=[],
        include_subfolders1=True,
        include_subfolders2=True,
        match_type="exact",
        images_only=False,
        include_masks=["*.bin"],
        exclude_masks=["skip.*"],
    )
    result = DuplicateFinder(config).scan()
    assert len(result.groups) == 1
    names = {entry.path.name for entry in result.groups[0].files}
    assert names == {"keep.bin", "also.bin"}
    assert result.search_roots == [root]


def test_scan_can_cancel(tmp_path: Path) -> None:
    root = tmp_path / "root"
    for index in range(20):
        _write(root / f"f{index}.bin", b"x" * (index + 1))

    config = SearchConfig(
        mode="single_list",
        list1_paths=[root],
        list2_paths=[],
        include_subfolders1=True,
        include_subfolders2=True,
        match_type="exact",
        images_only=False,
    )
    result = DuplicateFinder(config, cancel_check=lambda: True).scan()
    assert result.canceled is True


def test_duplicate_group_metrics() -> None:
    from src.core.models import DuplicateGroup, FileEntry, ScanResult

    group = DuplicateGroup(
        key="k",
        files=[
            FileEntry(path=Path("a"), size=10, mtime=1.0),
            FileEntry(path=Path("b"), size=10, mtime=2.0),
        ],
    )
    result = ScanResult(groups=[group], search_roots=[Path("root")])
    assert group.keep_suggestion == Path("a")
    assert result.duplicate_file_count == 1
    assert result.reclaimable_bytes == 10

    empty = ScanResult(
        groups=[DuplicateGroup(key="empty", files=[], keep_suggestion=None)],
    )
    assert empty.reclaimable_bytes == 0
