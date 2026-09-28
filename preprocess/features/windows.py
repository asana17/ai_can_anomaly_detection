"""Group consecutive moving rows of a grid into the inputs of a window model."""

from __future__ import annotations

import numpy as np


def positions(moving: np.ndarray, segment: np.ndarray) -> np.ndarray:
    """The count of consecutive moving rows so far, from 0. -1 where not moving.
    A new segment starts the count again."""
    moving = np.asarray(moving, bool)
    segment = np.asarray(segment)
    row = np.arange(len(moving))
    follows_moving = np.zeros(len(moving), bool)
    follows_moving[1:] = moving[:-1] & (segment[1:] == segment[:-1])
    first_row = np.maximum.accumulate(np.where(moving & ~follows_moving, row, 0))
    return np.where(moving, row - first_row, -1)


def window_ends(position: np.ndarray, *, rows: int, stride: int = 1) -> np.ndarray:
    """The indices of the last rows of the windows. The first window ends at the `rows`th
    row with no gap, and then one ends every `stride` rows."""
    after_first_end = np.asarray(position) - (rows - 1)
    return np.flatnonzero((after_first_end >= 0) & (after_first_end % stride == 0))


def window_rows(grid_rows: np.ndarray, ends: np.ndarray, *, rows: int) -> np.ndarray:
    """Each window as the `rows` rows of `grid_rows` up to its last row, oldest first."""
    return grid_rows[np.asarray(ends)[:, None] + np.arange(1 - rows, 1)]


def complete_window_ends(raw: np.ndarray, moving: np.ndarray, segment: np.ndarray, *,
                         rows: int, stride: int = 1) -> np.ndarray:
    """`window_ends` over the `moving` rows of `raw`, leaving out a window that holds a
    row with a NaN, a value J1939 reserves. It is left out rather than cut short, so the
    windows stay where the board places them."""
    complete = ~np.isnan(raw).any(axis=1)
    ends = window_ends(positions(moving, segment), rows=rows, stride=stride)
    return ends[window_rows(complete, ends, rows=rows).all(axis=1)]
