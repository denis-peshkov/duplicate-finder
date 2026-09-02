"""Тесты удаления с прогрессом."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.core.deleter import DeleteProgress, delete_to_recycle_bin


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
