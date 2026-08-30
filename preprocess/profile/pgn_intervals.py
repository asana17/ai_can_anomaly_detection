"""Collect arrival intervals for each (PGN, source address) stream."""

from __future__ import annotations

from typing import Iterable

from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame


def arrival_intervals(
    frames: Iterable[CanFrame],
) -> dict[tuple[int, int], list[float]]:
    last: dict[tuple[int, int], float] = {}
    intervals: dict[tuple[int, int], list[float]] = {}
    for frame in frames:
        ident = decompose_can_id(frame.can_id)
        key = (ident.pgn, ident.source_address)
        if key in last:
            intervals.setdefault(key, []).append(frame.timestamp - last[key])
        last[key] = frame.timestamp
    return intervals
