"""Decode all known SPNs of one frame into named physical values."""

from __future__ import annotations

from preprocess.frames.spn_decode import decode
from preprocess.frames.spn_spec import SPEC


def decode_frame(pgn: int, data: bytes) -> dict[str, float]:
    """Decode all of a PGN's SPNs to a {name: value} dict, skipping unavailable ones."""
    values = {}
    for spn in SPEC.get(pgn, ()):
        value = decode(data, spn.field)
        if value is not None:   # skip unavailable (0xFF) fields
            values[spn.name] = value
    return values
