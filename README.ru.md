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

- Python 3.12+
- Windows (основная платформа), код кроссплатформенный

## Установка

### Chocolatey (Windows)

```bash
choco install duplicate-finder
```

После установки в PATH появляется команда `duplicate-finder`.

### Homebrew (macOS)

Стабильный релиз (после принятия формулы в homebrew-core):

```bash
brew install duplicate-finder
```

Preview (`release/*` / `hotfix/*`):

```bash
brew tap denis-peshkov/duplicate-finder https://github.com/denis-peshkov/duplicate-finder --branch homebrew-preview-tap
brew install duplicate-finder-preview
```

### Из исходников

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

## Сборка (PyInstaller)

```bash
pip install pyinstaller
pyinstaller duplicate_finder.spec
```

- Windows: `dist/DuplicateFinder.exe`
- macOS: `dist/DuplicateFinder`

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
