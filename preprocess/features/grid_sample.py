"""Read the hold-last signal state into a row on a fixed time grid."""

from __future__ import annotations

from typing import Iterable, Iterator

from preprocess.features.signal_state import SignalState
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame
from preprocess.frames.frame_decode import decode_frame


def resample(
    frames: Iterable[CanFrame],
    period: float,
    max_hold: float,
) -> Iterator[tuple[float, list]]:
    """Emit (time, row) at each grid tick, holding the last value between frames.

    `max_hold` is the longest gap between frames the grid carries across. A longer
    gap means the recording stopped, so no rows are emitted across it and the grid
    restarts from the first frame after. The gap is measured on the bus rather than
    per signal. No stream here goes quiet while the others keep running.
    """
    state = SignalState()
    next_tick = None
    previous = None
    for f in frames:
        pgn = decompose_can_id(f.can_id).pgn
        if previous is not None and f.timestamp - previous > max_hold:
            state = SignalState()       # what it holds predates the gap
            next_tick = None
        while next_tick is not None and f.timestamp >= next_tick:
            if state.ready():
                yield (next_tick, state.row())
            next_tick += period
        state.update(decode_frame(pgn, f.data))
        previous = f.timestamp
        if next_tick is None:
            next_tick = f.timestamp + period
