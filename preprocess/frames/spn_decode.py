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
    if not (start_bit & 7) and not (length & 7):
        start = start_bit >> 3                # every SPN in the spec lands here
        return int.from_bytes(data[start:start + (length >> 3)], "little")
    value = 0
    for i in range(length):
        bit = start_bit + i
        byte_index = bit >> 3
        if byte_index < len(data) and (data[byte_index] >> (bit & 7)) & 1:
            value |= 1 << i
    return value


def decode(data: bytes, field: SpnField) -> float | None:
    """Decode one field to its physical value, or None where J1939 reserves the value."""
    raw = extract_le(data, field.start_bit, field.length)
    top_byte = raw >> max(field.length - 8, 0)
    if top_byte >= 0xFE:        # 0xFE marks an error, 0xFF marks not available
        return None
    return raw * field.scale + field.offset
