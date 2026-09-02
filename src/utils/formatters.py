"""Форматирование чисел для UI."""

from __future__ import annotations


def format_count(value: int) -> str:
    """Количество с разделителем тысяч через запятую: 1234567 → 1,234,567."""
    return f"{int(value):,}"
