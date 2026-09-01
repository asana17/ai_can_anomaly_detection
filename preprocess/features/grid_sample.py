"""Sample the hold-last signal state on a fixed time grid."""

from __future__ import annotations

from typing import Iterable, Iterator

from preprocess.features.signal_state import SignalState
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame
from preprocess.frames.frame_decode import decode_frame


def resample(frames: Iterable[CanFrame], period: float) -> Iterator[tuple[float, list]]:
    """Emit (time, snapshot) at each grid tick, holding the last value between frames."""
    state = SignalState()
    next_tick = None
    for f in frames:
        pgn = decompose_can_id(f.can_id).pgn
        while next_tick is not None and f.timestamp >= next_tick:
            if state.ready():
                yield (next_tick, state.snapshot())
            next_tick += period
        state.update(decode_frame(pgn, f.data))
        if next_tick is None:
            next_tick = f.timestamp + period
