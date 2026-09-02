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
