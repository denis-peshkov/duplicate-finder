"""Тесты enumerator."""

from __future__ import annotations

import os
from pathlib import Path

from src.core.enumerator import enumerate_paths, format_list_item, parse_list_item


def test_parse_list_item_folder_suffix() -> None:
    path, is_folder = parse_list_item(rf"P:\data\*")
    assert is_folder is True
    assert path == Path(r"P:\data")


def test_parse_list_item_folder_suffix_forward_slash() -> None:
    path, is_folder = parse_list_item("data/*")
    assert is_folder is True
    assert path == Path("data")


def test_format_list_item_folder() -> None:
    assert format_list_item(Path("data"), True) == f"data{os.sep}*"


def test_enumerate_with_subfolders(tmp_path: Path) -> None:
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)
    file_a = root / "a.txt"
    file_b = sub / "b.txt"
    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")

    items = [format_list_item(root, True)]
    entries = enumerate_paths(items, include_subfolders=True, images_only=False, source="list1")
    paths = {entry.path.name for entry in entries}
    assert paths == {"a.txt", "b.txt"}


def test_enumerate_without_subfolders(tmp_path: Path) -> None:
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)
    (root / "a.txt").write_text("a", encoding="utf-8")
    (sub / "b.txt").write_text("b", encoding="utf-8")

    items = [format_list_item(root, True)]
    entries = enumerate_paths(items, include_subfolders=False, images_only=False, source="list1")
    paths = {entry.path.name for entry in entries}
    assert paths == {"a.txt"}


def test_enumerate_images_only(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "photo.jpg").write_bytes(b"jpg")
    (root / "doc.txt").write_text("txt", encoding="utf-8")

    items = [format_list_item(root, True)]
    entries = enumerate_paths(items, include_subfolders=True, images_only=True, source="list1")
    assert len(entries) == 1
    assert entries[0].path.name == "photo.jpg"


def test_enumerate_exclude_masks(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "keep.txt").write_text("a", encoding="utf-8")
    (root / "skip.tmp").write_text("b", encoding="utf-8")
    (root / "Thumbs.db").write_bytes(b"x")

    items = [format_list_item(root, True)]
    entries = enumerate_paths(
        items,
        include_subfolders=True,
        images_only=False,
        source="list1",
        exclude_masks=["*.tmp", "Thumbs.db"],
    )
    names = {entry.path.name for entry in entries}
    assert names == {"keep.txt"}


def test_enumerate_include_masks(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    (root / "b.jpg").write_text("b", encoding="utf-8")
    (root / "c.png").write_text("c", encoding="utf-8")

    items = [format_list_item(root, True)]
    entries = enumerate_paths(
        items,
        include_subfolders=True,
        images_only=False,
        source="list1",
        include_masks=["*.jpg", "*.png"],
    )
    names = {entry.path.name for entry in entries}
    assert names == {"b.jpg", "c.png"}


def test_enumerate_include_then_exclude(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "keep.jpg").write_text("a", encoding="utf-8")
    (root / "drop.tmp.jpg").write_text("b", encoding="utf-8")
    (root / "other.txt").write_text("c", encoding="utf-8")

    items = [format_list_item(root, True)]
    entries = enumerate_paths(
        items,
        include_subfolders=True,
        images_only=False,
        source="list1",
        include_masks=["*.jpg"],
        exclude_masks=["*.tmp.jpg"],
    )
    names = {entry.path.name for entry in entries}
    assert names == {"keep.jpg"}


def test_matches_exclude_mask_path_pattern(tmp_path: Path) -> None:
    from src.core.enumerator import matches_exclude_mask

    nested = tmp_path / ".git" / "config"
    nested.parent.mkdir(parents=True)
    nested.write_text("x", encoding="utf-8")
    assert matches_exclude_mask(nested, ["*/.git/*"]) is True
    assert matches_exclude_mask(tmp_path / "a.txt", ["*/.git/*"]) is False


def test_matches_mask_skips_blank_and_name_patterns(tmp_path: Path) -> None:
    from src.core.enumerator import matches_mask, should_keep_file

    path = tmp_path / "photo.jpg"
    path.write_bytes(b"x")
    assert matches_mask(path, ["", "  ", "*.jpg"]) is True
    assert matches_mask(path, ["*.png"]) is False
    assert should_keep_file(path, include_masks=["*.jpg"], exclude_masks=None) is True
    assert should_keep_file(path, include_masks=["*.png"], exclude_masks=None) is False


def test_enumerate_single_file_and_missing(tmp_path: Path) -> None:
    file_path = tmp_path / "solo.txt"
    file_path.write_text("x", encoding="utf-8")
    missing = tmp_path / "gone.txt"

    seen: list[str] = []
    entries = enumerate_paths(
        [str(file_path), str(missing)],
        include_subfolders=False,
        images_only=False,
        source="list1",
        on_file=lambda entry: seen.append(entry.path.name),
    )
    assert len(entries) == 1
    assert seen == ["solo.txt"]


def test_enumerate_can_cancel(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    for index in range(5):
        (root / f"f{index}.txt").write_text("x", encoding="utf-8")

    calls = {"n": 0}

    def on_file(_entry) -> None:
        calls["n"] += 1

    entries = enumerate_paths(
        [format_list_item(root, True)],
        include_subfolders=True,
        images_only=False,
        source="list1",
        on_file=on_file,
        cancel_check=lambda: calls["n"] >= 2,
    )
    assert len(entries) == 2


def test_enumerate_images_only_single_file(tmp_path: Path) -> None:
    image = tmp_path / "a.jpg"
    text = tmp_path / "b.txt"
    image.write_bytes(b"jpg")
    text.write_text("t", encoding="utf-8")

    entries = enumerate_paths(
        [str(image), str(text)],
        include_subfolders=False,
        images_only=True,
        source="list1",
    )
    assert len(entries) == 1
    assert entries[0].path.name == "a.jpg"


def test_enumerate_dir_without_folder_marker(tmp_path: Path) -> None:
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)
    (root / "a.txt").write_text("a", encoding="utf-8")
    (sub / "b.txt").write_text("b", encoding="utf-8")
    (root / "skip.jpg").write_bytes(b"j")

    entries = enumerate_paths(
        [str(root)],
        include_subfolders=False,
        images_only=False,
        source="list1",
        exclude_masks=["*.jpg"],
    )
    names = {entry.path.name for entry in entries}
    assert names == {"a.txt"}


def test_enumerate_single_file_respects_masks(tmp_path: Path) -> None:
    keep = tmp_path / "keep.bin"
    drop = tmp_path / "drop.tmp"
    keep.write_bytes(b"1")
    drop.write_bytes(b"2")

    entries = enumerate_paths(
        [str(keep), str(drop)],
        include_subfolders=False,
        images_only=False,
        source="list1",
        include_masks=["*.bin"],
        exclude_masks=["drop.*"],
    )
    assert len(entries) == 1
    assert entries[0].path.name == "keep.bin"
