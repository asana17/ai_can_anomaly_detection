"""Which rows raise an alarm, from the model's scores and the rule hits."""

from __future__ import annotations

import numpy as np


def persistent(flag, segment, need):
    """True where `need` rows in a row are flagged, without crossing a segment."""
    if need <= 1:
        return flag
    out, run = np.zeros(len(flag), bool), 0
    for i in range(len(flag)):
        run = run + 1 if flag[i] and i and segment[i] == segment[i - 1] else int(flag[i])
        out[i] = run >= need
    return out


def alarmed_rows(scores, threshold, rule_hit, segment, hold):
    """True where `hold` rows in a row have a rule hit or a score above `threshold`.

    A row the model did not score has a NaN score, which is never above it.
    """
    return persistent((scores > threshold) | rule_hit, segment, hold)
