# Duplicate Finder

Desktop-приложение для поиска и удаления дубликатов файлов.

## Возможности

- Поиск дубликатов в одном списке путей или сравнение двух списков
- Режимы: exact duplicate (по хешу) и same filename
- Фильтр «только изображения»
- Обход подпапок для каждого списка
- Прогресс сканирования с отменой
- Удаление выбранных файлов в корзину (Recycle Bin)

## Требования

- Python 3.11+
- Windows (основная платформа), код кроссплатформенный

## Установка

```bash
cd duplicate-finder
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Запуск

```bash
python main.py
```

## Тесты

```bash
pytest
```

## Сборка exe (PyInstaller)

```bash
pip install pyinstaller
pyinstaller duplicate_finder.spec
```

Исполняемый файл будет в `dist/DuplicateFinder.exe`.

## Настройки

Файл: `%USERPROFILE%\.duplicate-finder\settings.toml`

Логи: `%USERPROFILE%\.duplicate-finder\duplicate-finder.log`

## Структура

```
duplicate-finder/
  main.py
  src/
    config/     — настройки
    core/       — поиск, хеширование, удаление
    ui/         — CustomTkinter интерфейс
    utils/      — логирование
  tests/
```

## Лицензия

MIT
