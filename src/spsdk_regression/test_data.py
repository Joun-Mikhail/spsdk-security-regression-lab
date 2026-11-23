"""Deterministic synthetic test inputs and controlled mutations.

The "firmware" here is just reproducible binary bytes that stand in for an image; it is never
executed. Using fixed seeds makes every failure reproducible.
"""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

FIRMWARE_SIZES = (1, 256, 4096)


def synthetic_firmware(size: int, seed: int = 0x5EC0DE) -> bytes:
    """Return ``size`` deterministic pseudo-random bytes (full 0x00-0xFF range)."""
    if size < 0:
        raise ValueError("size must be non-negative")
    # Not used for anything security-relevant: only to generate repeatable test data.
    return random.Random(seed).randbytes(size)  # noqa: S311


def flip_byte(data: bytes, index: int, mask: int = 0x01) -> bytes:
    """Return a copy of ``data`` with exactly one byte changed (XOR with ``mask``)."""
    if not data:
        raise ValueError("cannot flip a byte in empty data")
    if mask == 0 or not 0 <= mask <= 0xFF:
        raise ValueError("mask must be in 1..255 so the byte really changes")
    mutated = bytearray(data)
    mutated[index] ^= mask
    return bytes(mutated)


def write_bytes(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


def sha256_hex(data: bytes) -> str:
    """Independent SHA-256 oracle (Python hashlib)."""
    return hashlib.sha256(data).hexdigest()


def corrupt_hex_digit(hex_digest: str, position: int = 0) -> str:
    """Change exactly one hexadecimal character of a digest string."""
    original = hex_digest[position]
    replacement = "0" if original != "0" else "1"
    return hex_digest[:position] + replacement + hex_digest[position + 1 :]
