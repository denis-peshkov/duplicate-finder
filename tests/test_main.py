"""Тесты точки входа."""

from __future__ import annotations

from src.config.app_info import APP_NAME, APP_VERSION


def test_main_version(capsys, monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["duplicate-finder", "--version"])
    from main import main

    main()
    out = capsys.readouterr().out.strip()
    assert out == f"{APP_NAME} {APP_VERSION}"
