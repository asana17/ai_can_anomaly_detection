"""The grid every row sits on, set in one place so no caller can pick another."""

from __future__ import annotations

import numpy as np

from preprocess.features.grid_sample import DEFAULT_MAX_HOLD, DEFAULT_PERIOD

PERIOD = DEFAULT_PERIOD
MAX_HOLD = DEFAULT_MAX_HOLD


def starts_segment(previous, t: float) -> bool:
    """True where a row begins a segment, at the first row or after a gap."""
    return previous is None or t - previous > PERIOD * 1.5


def to_arrays(rows, times, segments) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The three lists as arrays, in the dtypes the rest of the pipeline reads."""
    return (
        np.asarray(rows, dtype=np.float32),
        np.asarray(times, dtype=np.float64),    # epoch seconds need the precision
        np.asarray(segments, dtype=np.int32),
    )
