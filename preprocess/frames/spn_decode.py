"""Extract one J1939 SPN field from a payload as a physical value."""

from __future__ import annotations

from typing import NamedTuple


class SpnField(NamedTuple):
    start_bit: int
    length: int
    scale: float
    offset: float


def extract_le(data: bytes, start_bit: int, length: int) -> int:
    """Read `length` bits at `start_bit` as an unsigned little-endian integer."""
    value = 0
    for i in range(length):
        bit = start_bit + i
        byte_index = bit >> 3
        if byte_index < len(data) and (data[byte_index] >> (bit & 7)) & 1:
            value |= 1 << i
    return value


def decode(data: bytes, field: SpnField) -> float | None:
    """Decode one field to its physical value, or None if the field is all ones."""
    raw = extract_le(data, field.start_bit, field.length)
    if raw == (1 << field.length) - 1:   # all bits set means not available
        return None
    return raw * field.scale + field.offset
