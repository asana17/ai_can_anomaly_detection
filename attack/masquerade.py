"""Masquerade: overwrite signal values in place within a window, keeping timing."""

from __future__ import annotations

from typing import Iterable

from attack.spn_encode import set_field
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame
from preprocess.frames.spn_spec import SPEC


def _names_to_fields(changes: dict[int, dict[str, float]]):
    # {pgn: {name: value}} -> {pgn: [(field, value), ...]}
    out = {}
    for pgn, signals in changes.items():
        by_name = {d.name: d.field for d in SPEC[pgn]}
        out[pgn] = [(by_name[name], value) for name, value in signals.items()]
    return out


def masquerade(
    frames: Iterable[CanFrame],
    changes: dict[int, dict[str, float]],
    start: float,
    stop: float,
) -> list[CanFrame]:
    """Overwrite the signals in `changes` on frames of those PGNs within [start, stop]."""
    field_changes = _names_to_fields(changes)
    out = []
    for f in frames:
        pgn = decompose_can_id(f.can_id).pgn
        if start <= f.timestamp <= stop and pgn in field_changes:
            data = f.data
            for field, value in field_changes[pgn]:
                data = set_field(data, field, value)
            out.append(CanFrame(f.timestamp, f.can_id, data))
        else:
            out.append(f)
    return out
