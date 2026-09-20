"""Read logs into one row per tick of a fixed time grid, holding the last value.

The frames of a log arrive at their own rates. A row every `PERIOD` seconds, each
column the last value that signal carried, is what a model and a rule read instead.
"""

from __future__ import annotations

import numpy as np

from preprocess.features.grid_sample import resample
from preprocess.features.signal_state import SIGNALS
from preprocess.frames.can_log_loader import load_can_log


def moving(raw: np.ndarray, *, min_speed: float) -> np.ndarray:
    """True where a row's wheel speed is above `min_speed`, read off physical values."""
    return raw[:, SIGNALS.index("wheel_speed")] > min_speed


def starts_segment(previous, t: float, *, period: float) -> bool:
    """True where a row begins a segment, at the first row or after a gap."""
    return previous is None or t - previous > period * 1.5


def to_arrays(rows, times, segments) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The three lists as arrays, in the dtypes the rest of the pipeline reads."""
    return (
        np.asarray(rows, dtype=np.float32),
        np.asarray(times, dtype=np.float64),    # epoch seconds need the precision
        np.asarray(segments, dtype=np.int32),
    )


def grid_rows(logs, *, period: float, max_hold: float):
    """Read every log into rows, one per tick, with their times and segment ids."""
    rows, times, segments = [], [], []
    segment = -1
    for path in logs:
        previous = None
        for t, row in resample(load_can_log(path), period, max_hold):
            if starts_segment(previous, t, period=period):
                segment += 1                # a new log, or the grid restarted
            rows.append(row)
            times.append(t)
            segments.append(segment)
            previous = t
    return to_arrays(rows, times, segments)
