"""Тесты удаления с прогрессом."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.core.deleter import DeleteProgress, delete_to_recycle_bin, remove_empty_folders


def test_delete_reports_progress(tmp_path: Path) -> None:
    files = [tmp_path / f"a{i}.txt" for i in range(3)]
    for path in files:
        path.write_text("x", encoding="utf-8")

    events: list[DeleteProgress] = []

    with patch("src.core.deleter.send2trash") as mocked:
        result = delete_to_recycle_bin(
            files,
            progress_callback=events.append,
        )

    assert mocked.call_count == 3
    assert len(result.deleted) == 3
    assert len(events) == 3
    assert events[-1].current == 3
    assert events[-1].total == 3


def test_delete_can_cancel(tmp_path: Path) -> None:
    files = [tmp_path / f"b{i}.txt" for i in range(5)]
    for path in files:
        path.write_text("x", encoding="utf-8")

    calls = {"n": 0}

    def cancel_after_two() -> bool:
        return calls["n"] >= 2

    def on_progress(progress: DeleteProgress) -> None:
        calls["n"] = progress.current

    with patch("src.core.deleter.send2trash"):
        result = delete_to_recycle_bin(
            files,
            progress_callback=on_progress,
            cancel_check=cancel_after_two,
        )

    assert result.canceled is True
    assert len(result.deleted) == 2


def test_remove_empty_folders_walks_all_roots(tmp_path: Path) -> None:
    root = tmp_path / "scan_root"
    nested = root / "a" / "b"
    nested.mkdir(parents=True)
    orphan = root / "empty_orphan" / "deep"
    orphan.mkdir(parents=True)
    kept = root / "with_file"
    kept.mkdir()
    (kept / "stay.txt").write_text("y", encoding="utf-8")

    def fake_trash(path: str) -> None:
        Path(path).rmdir()

    with patch("src.core.deleter.send2trash", side_effect=fake_trash):
        removed, failed = remove_empty_folders(roots=[root])

    assert not failed
    assert nested in removed
    assert (root / "a") in removed
    assert orphan in removed
    assert (root / "empty_orphan") in removed
    assert kept not in removed
    assert root not in removed
    assert root.exists()
    assert (kept / "stay.txt").exists()


def test_remove_empty_folders_reports_progress(tmp_path: Path) -> None:
    root = tmp_path / "scan_root"
    (root / "a" / "b").mkdir(parents=True)
    (root / "c").mkdir(parents=True)

    events: list[DeleteProgress] = []

    def fake_trash(path: str) -> None:
        Path(path).rmdir()

    with patch("src.core.deleter.send2trash", side_effect=fake_trash):
        removed, failed = remove_empty_folders(
            roots=[root],
            progress_callback=events.append,
        )

    assert not failed
    assert len(removed) >= 2
    assert events
    assert all(event.phase == "folders" for event in events)
    assert events[-1].folders_removed == len(removed)
    assert events[-1].folders_scanned >= len(removed)


def test_remove_empty_folders_keeps_folder_with_files(tmp_path: Path) -> None:
    root = tmp_path / "scan_root"
    folder = root / "mixed"
    folder.mkdir(parents=True)
    (folder / "stay.txt").write_text("y", encoding="utf-8")

    with patch("src.core.deleter.send2trash") as mocked:
        removed, failed = remove_empty_folders(roots=[root])

    assert removed == []
    assert failed == []
    assert mocked.call_count == 0
    assert (folder / "stay.txt").exists()
