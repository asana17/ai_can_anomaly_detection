"""Which rows raise an alarm, from the model's scores and the rule hits."""

from __future__ import annotations

import numpy as np


def k_of_last_n(flag, segment, n, k):
    """True where `k` of the last `n` rows are flagged, without crossing a segment.

    Near the start of a segment the rows it has so far are counted.
    """
    flag = np.asarray(flag, bool)
    if not len(flag):
        return flag
    at = np.arange(len(flag))
    starts = np.r_[True, segment[1:] != segment[:-1]]
    start = np.maximum.accumulate(np.where(starts, at, 0))
    total = np.r_[0, np.cumsum(flag)]
    return total[at + 1] - total[np.maximum(at + 1 - n, start)] >= k


def alarmed_rows(scores, threshold, rule_hit, segment, n, k):
    """True where `k` of the last `n` rows have a rule hit or a score above
    `threshold`."""
    return k_of_last_n(flagged_rows(scores, threshold, rule_hit), segment, n, k)


def flagged_rows(scores, threshold, rule_hit):
    """True where a row has a rule hit or a score above `threshold`.

    A row the model did not score has a NaN score, which is never above it.
    """
    return (scores > threshold) | rule_hit


def windows_with_k_flagged(flag, ends, rows, k):
    """For each window, True when `k` of its `rows` rows are flagged.

    A window is given by the index of its last row, and holds that row and the
    `rows - 1` before it.
    """
    total = np.r_[0, np.cumsum(np.asarray(flag, bool))]
    ends = np.asarray(ends)
    return total[ends + 1] - total[ends + 1 - rows] >= k


def windows_above(window_scores, threshold, ends):
    """For each window, given by the index of its last row, True when its score is
    above `threshold`."""
    return window_scores[np.asarray(ends)] > threshold
