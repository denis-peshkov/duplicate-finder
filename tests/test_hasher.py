"""Тесты хеширования файлов."""

from __future__ import annotations

from pathlib import Path

from src.core.hasher import PARTIAL_CHUNK_SIZE, full_hash, hash_file, partial_hash


def test_partial_and_full_hash_stable(tmp_path: Path) -> None:
    path = tmp_path / "data.bin"
    path.write_bytes(b"abc" * 100)

    assert partial_hash(path) == partial_hash(path)
    assert full_hash(path) == hash_file(path)
    assert partial_hash(path)
    assert hash_file(path)


def test_partial_hash_reads_tail_for_large_file(tmp_path: Path) -> None:
    path = tmp_path / "large.bin"
    payload = (b"H" * PARTIAL_CHUNK_SIZE) + (b"M" * 100) + (b"T" * PARTIAL_CHUNK_SIZE)
    path.write_bytes(payload)

    digest = partial_hash(path)
    assert digest
    assert len(digest) == 32


def test_partial_hash_medium_file(tmp_path: Path) -> None:
    path = tmp_path / "medium.bin"
    path.write_bytes(b"x" * (PARTIAL_CHUNK_SIZE + 50))
    assert partial_hash(path)


def test_hash_cancel_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "big.bin"
    path.write_bytes(b"z" * (PARTIAL_CHUNK_SIZE * 3))

    assert partial_hash(path, cancel_check=lambda: True) == ""
    assert full_hash(path, cancel_check=lambda: True) == ""
    assert hash_file(path, cancel_check=lambda: True) == ""


def test_hash_missing_file_returns_empty(tmp_path: Path) -> None:
    missing = tmp_path / "gone.bin"
    assert partial_hash(missing) == ""
    assert hash_file(missing) == ""
