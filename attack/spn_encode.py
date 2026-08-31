"""Write a physical value into a payload, the inverse of preprocess spn_decode."""

from __future__ import annotations

from preprocess.frames.spn_decode import SpnField


def encode(value: float, field: SpnField) -> int:
    raw = round((value - field.offset) / field.scale)
    return max(0, min(raw, (1 << field.length) - 1))


def set_field(data: bytes, field: SpnField, value: float) -> bytes:
    """Return a copy of data with this field's bits overwritten to encode value."""
    raw = encode(value, field)
    buf = bytearray(data)
    for i in range(field.length):   # write raw little-endian, bit by bit
        pos = field.start_bit + i
        mask = 1 << (pos & 7)
        if (raw >> i) & 1:
            buf[pos >> 3] |= mask
        else:
            buf[pos >> 3] &= ~mask
    return bytes(buf)
