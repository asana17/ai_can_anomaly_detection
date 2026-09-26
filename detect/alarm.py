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
    """True where `k` of the last `n` rows have a rule hit or a score above `threshold`.

    A row the model did not score has a NaN score, which is never above it.
    """
    return k_of_last_n((scores > threshold) | rule_hit, segment, n, k)
