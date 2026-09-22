"""Read the hold-last signal state into a row on a fixed time grid."""

from __future__ import annotations

from typing import Iterable, Iterator

from preprocess.features.signal_state import SignalState
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame


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

    A tick with no frame since the tick before gets no row, since the row would hold
    only old values. The board takes its rows as the bus runs, and cannot yet tell a
    short silence from one longer than `max_hold`, so it drops those rows the same way.
    """
    state = SignalState()
    next_tick = None
    previous = None
    fresh = False       # a frame has arrived since the last tick
    for f in frames:
        pgn = decompose_can_id(f.can_id).pgn
        if previous is not None and f.timestamp - previous > max_hold:
            state = SignalState()       # what it holds predates the gap
            next_tick = None
        while next_tick is not None and f.timestamp >= next_tick:
            if fresh and state.ready():
                yield (next_tick, state.row())
            fresh = False
            next_tick += period
        state.update(pgn, f.data)
        fresh = True
        previous = f.timestamp
        if next_tick is None:
            next_tick = f.timestamp + period
