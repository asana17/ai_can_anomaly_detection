"""How many alarms a detector raised, and which attacks they landed in."""

from __future__ import annotations

import numpy as np


def count_alarms(alarmed):
    """How many separate stretches of alarmed rows there are."""
    return int((alarmed & ~np.concatenate([[False], alarmed[:-1]])).sum())


def attacks_with_a_flagged_row(flagged, attacks):
    """For each attack, whether any of its rows is flagged."""
    return np.array([flagged[a["first"]:a["last"] + 1].any() for a in attacks],
                    dtype=bool)
