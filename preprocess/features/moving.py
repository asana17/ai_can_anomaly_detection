"""Mark the rows whose wheel speed is above a given speed."""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS


def moving(raw: np.ndarray, *, min_speed: float) -> np.ndarray:
    """True where a row's wheel speed is above `min_speed`, read off physical values."""
    return raw[:, SIGNALS.index("wheel_speed")] > min_speed


def moving_spans(rows, *, min_speed: float, period: float) -> list[tuple[float, float]]:
    """The first and last times of each run of `rows` that are `moving`, `rows` being a
    log's rows by time. A run ends where a row is missing."""
    if not rows:
        return []
    times = list(rows)
    keep = moving(np.asarray(list(rows.values())), min_speed=min_speed)
    spans, start = [], None
    for i, (t, go) in enumerate(zip(times, keep)):
        if start is not None and (not go or t - times[i - 1] > period * 1.5):
            spans.append((start, times[i - 1]))
            start = None
        if go and start is None:
            start = t
    if start is not None:
        spans.append((start, times[-1]))
    return spans
