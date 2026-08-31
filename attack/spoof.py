"""Spoof: overwrite one signal to a fixed value within a time window."""

from __future__ import annotations

from typing import Iterable

from attack.spn_encode import set_field
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame
from preprocess.frames.spn_spec import SPEC


def spoof(
    frames: Iterable[CanFrame],
    pgn: int,
    name: str,
    value: float,
    start: float,
    stop: float,
) -> list[CanFrame]:
    field = next(d for d in SPEC[pgn] if d.name == name).field
    out = []
    for f in frames:
        if start <= f.timestamp <= stop and decompose_can_id(f.can_id).pgn == pgn:
            out.append(CanFrame(f.timestamp, f.can_id, set_field(f.data, field, value)))
        else:
            out.append(f)
    return out
