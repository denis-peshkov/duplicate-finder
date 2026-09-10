"""Тесты загрузки и сохранения настроек."""

from __future__ import annotations

from pathlib import Path

from src.config.settings import Settings, load_settings, save_settings


def test_load_settings_missing_file(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "missing.toml")
    assert settings == Settings()


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    original = Settings(
        window_width=1200,
        include_masks=["*.jpg"],
        exclude_masks=["*.tmp"],
        clean_empty_folders=False,
        list1_paths=["/tmp/a"],
    )
    save_settings(original, path)

    loaded = load_settings(path)
    assert loaded.window_width == 1200
    assert loaded.include_masks == ["*.jpg"]
    assert loaded.exclude_masks == ["*.tmp"]
    assert loaded.clean_empty_folders is False
    assert loaded.list1_paths == ["/tmp/a"]


def test_load_settings_ignores_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    path.write_text('window_width = 900\nunknown_key = "x"\n', encoding="utf-8")

    loaded = load_settings(path)
    assert loaded.window_width == 900
    assert not hasattr(loaded, "unknown_key")


def test_load_settings_invalid_toml(tmp_path: Path) -> None:
    path = tmp_path / "broken.toml"
    path.write_text("not = [valid", encoding="utf-8")

    loaded = load_settings(path)
    assert loaded == Settings()
