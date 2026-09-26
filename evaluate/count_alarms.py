"""How many alarms a detector raised, and which attacks they landed in."""

from __future__ import annotations

import numpy as np


def count_alarms(alarmed):
    """How many separate stretches of alarmed rows there are."""
    return int((alarmed & ~np.concatenate([[False], alarmed[:-1]])).sum())


def count_false_positive_alarms(alarmed, attacks):
    """How many alarms have no row of an attack in them.

    An alarm is a stretch of alarmed rows. One that starts in an attack and goes on
    after the attack ends is not a false positive.
    """
    attacked = np.zeros(len(alarmed), bool)
    for a in attacks:
        attacked[a["first"]:a["last"] + 1] = True
    starts = alarmed & ~np.concatenate([[False], alarmed[:-1]])
    alarm = np.cumsum(starts)               # the number of the alarm each row is in
    with_attack = np.unique(alarm[alarmed & attacked])
    return int(starts.sum() - len(with_attack))


def attacks_with_a_flagged_row(flagged, attacks):
    """For each attack, whether any of its rows is flagged."""
    return np.array([flagged[a["first"]:a["last"] + 1].any() for a in attacks],
                    dtype=bool)
