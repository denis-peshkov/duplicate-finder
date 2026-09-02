#!/usr/bin/env python3
"""
Точка входа в приложение Duplicate Finder.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import load_settings, save_settings
from src.ui.app import DuplicateFinderApp
from src.utils.logger import setup_logging


def main() -> None:
    """Главная функция запуска приложения."""
    log_dir = Path.home() / ".duplicate-finder"
    log_file = log_dir / "duplicate-finder.log"
    setup_logging(log_file=log_file, level=logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Duplicate Finder v0.1.0")
    logger.info("=" * 60)

    settings = load_settings()

    if settings.first_run:
        logger.info("Первый запуск приложения")
        settings.first_run = False
        save_settings(settings)

    try:
        app = DuplicateFinderApp(settings)
        app.run()
    except Exception as exc:
        logger.critical("Критическая ошибка: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
