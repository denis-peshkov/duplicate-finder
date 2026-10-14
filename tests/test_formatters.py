"""Тесты форматирования."""

from src.utils.formatters import format_count, format_duration


def test_format_count_thousands() -> None:
    assert format_count(0) == "0"
    assert format_count(12) == "12"
    assert format_count(1234) == "1,234"
    assert format_count(1234567) == "1,234,567"


def test_format_duration() -> None:
    assert format_duration(0) == "0:00"
    assert format_duration(65) == "1:05"
    assert format_duration(3661) == "1:01:01"
    assert format_duration(-5) == "0:00"
