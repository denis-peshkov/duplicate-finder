"""Форматирование чисел для UI."""

from __future__ import annotations


def format_count(value: int) -> str:
    """Количество с разделителем тысяч через запятую: 1234567 → 1,234,567."""
    return f"{int(value):,}"


def format_duration(seconds: float) -> str:
    """Длительность как H:MM:SS или M:SS."""
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
