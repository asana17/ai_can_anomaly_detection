"""How many alarms a detector raised, and which attacks they landed in."""

from __future__ import annotations

import numpy as np


def attack_row_mask(attacks, length):
    """Which rows are in an attack, one flag per row of a set with `length` rows.

    A row is flagged when it lies between an attack's first and last row.
    """
    attacked = np.zeros(length, bool)
    for a in attacks:
        attacked[a["first"]:a["last"] + 1] = True
    return attacked


def count_false_positive_alarms(alarmed, attacked):
    """Count the false positive alarms.

    `alarmed` and `attacked` hold one flag per row. An alarm is a stretch of rows
    `alarmed` flags. It is a false positive when `attacked` flags none of its rows.
    """
    starts = alarmed & ~np.concatenate([[False], alarmed[:-1]])
    alarm = np.cumsum(starts)               # the number of the alarm each row is in
    with_attack = np.unique(alarm[alarmed & attacked])
    return int(starts.sum() - len(with_attack))


def attacks_with_a_flagged_row(flagged, attacks):
    """For each attack, whether any of its rows is flagged."""
    return np.array([flagged[a["first"]:a["last"] + 1].any() for a in attacks],
                    dtype=bool)
