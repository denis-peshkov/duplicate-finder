"""
Модуль управления настройками приложения.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import tomllib as tomli
import tomli_w

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path.home() / ".duplicate-finder"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "settings.toml"


@dataclass
class Settings:
    """Настройки приложения."""

    window_width: int = 1100
    window_height: int = 720
    first_run: bool = True

    search_mode: str = "single_list"
    match_type: str = "exact"
    images_only: bool = False
    include_subfolders1: bool = True
    include_subfolders2: bool = True

    list1_paths: list[str] = field(default_factory=list)
    list2_paths: list[str] = field(default_factory=list)


def load_settings(config_path: Optional[Path] = None) -> Settings:
    """Загрузка настроек из TOML-файла."""
    path = config_path or DEFAULT_CONFIG_PATH

    if not path.exists():
        logger.info("Файл настроек не найден: %s, используются настройки по умолчанию", path)
        return Settings()

    try:
        with open(path, "rb") as handle:
            data = tomli.load(handle)

        known_fields = {key for key in asdict(Settings())}
        filtered_data = {key: value for key, value in data.items() if key in known_fields}
        settings = Settings(**filtered_data)
        logger.info("Настройки загружены: %s", path)
        return settings
    except (tomli.TOMLDecodeError, OSError, TypeError) as exc:
        logger.warning("Ошибка загрузки настроек: %s", exc)
        return Settings()


def save_settings(settings: Settings, config_path: Optional[Path] = None) -> None:
    """Сохранение настроек в TOML-файл."""
    path = config_path or DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, "wb") as handle:
            tomli_w.dump(asdict(settings), handle)
        logger.info("Настройки сохранены: %s", path)
    except (OSError, TypeError) as exc:
        logger.error("Ошибка сохранения настроек: %s", exc)
