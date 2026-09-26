"""How many alarms a detector raised, and which attacks they landed in."""

from __future__ import annotations

import numpy as np


def count_false_positive_alarms(alarmed, attacks):
    """How many alarms have no row of an attack in them.

    An alarm is a stretch of alarmed rows. One that starts in an attack and goes on
    after the attack ends is not a false positive.
    """
    starts = alarmed & ~np.concatenate([[False], alarmed[:-1]])
    return alarms_with_no_attack(starts, alarmed,
                                 rows_in_an_attack(len(alarmed), attacks))


def attacks_with_a_flagged_row(flagged, attacks):
    """For each attack, whether any of its rows is flagged."""
    return np.array([flagged[a["first"]:a["last"] + 1].any() for a in attacks],
                    dtype=bool)


def count_false_positive_window_alarms(alarmed, ends, position, stride, attacks):
    """How many alarms of a window model have no window that ends in an attack.

    A window is given by the index of its last row, `ends`. An alarm is alarmed windows
    one after the other, where the next window ends `stride` rows later in the same
    unbroken span of moving rows. `position` is the count of moving rows so far, as
    `preprocess.features.windows.positions` gives it.
    """
    ends = np.asarray(ends)
    alarmed = np.asarray(alarmed, bool)
    follows = (np.diff(ends) == stride) & (np.diff(position[ends]) == stride)
    starts = alarmed & ~np.concatenate([[False], follows & alarmed[:-1]])
    return alarms_with_no_attack(starts, alarmed,
                                 rows_in_an_attack(len(position), attacks)[ends])


def alarms_with_no_attack(starts, alarmed, attacked):
    """How many alarms have nothing `attacked` in them, where `starts` marks where each
    alarm starts."""
    alarm = np.cumsum(starts)               # the number of the alarm each one is in
    return int(starts.sum() - len(np.unique(alarm[alarmed & attacked])))


def rows_in_an_attack(rows, attacks):
    """True on the rows, of `rows`, that are in one of `attacks`."""
    attacked = np.zeros(rows, bool)
    for a in attacks:
        attacked[a["first"]:a["last"] + 1] = True
    return attacked
