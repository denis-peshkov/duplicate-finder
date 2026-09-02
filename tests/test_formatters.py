"""Тесты форматирования."""

from src.utils.formatters import format_count


def test_format_count_thousands() -> None:
    assert format_count(0) == "0"
    assert format_count(12) == "12"
    assert format_count(1234) == "1,234"
    assert format_count(1234567) == "1,234,567"
