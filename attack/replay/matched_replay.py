"""Pick a replay from a donor moment that held this log's speed and gear."""

from __future__ import annotations

import random
from typing import Iterable

import numpy as np

from attack.replay.options import PGNS, SECONDS, pgns_of, time_in
from attack.replay.replay import write_replay
from preprocess.features.signal_state import SIGNALS
from preprocess.frames.can_log_loader import CanFrame
from rules.instant.speed_agreement import MAX_DISAGREEMENT

# The PGNs a matched replay fakes. CCVS1 and ETC2 carry the signals the donor is
# matched on, so replaying them writes back close to what was there.
MATCHED_PGNS = tuple(pgn for pgn in PGNS if pgn not in (65265, 61445))

# What the donor is matched on, the speed to `MAX_DISAGREEMENT` and the gear exactly.
MATCHED = ("wheel_speed", "current_gear")

def matched_sources(rows: dict, source_rows: dict, start: float, stop: float, *,
                    period: float, tolerance: float = MAX_DISAGREEMENT) -> list:
    """The times in `source_rows` a replay of [start, stop] can copy from.

    A time matches when the donor holds this log's speed within `tolerance` and its gear
    exactly, on every row of the stretch, with no row of its own missing. Both arguments
    are a log's rows by time, as a grid holds them.
    """
    here = sorted(t for t in rows if start <= t <= stop)
    there = sorted(source_rows)
    if not here or len(there) < len(here):
        return []
    columns = [SIGNALS.index(name) for name in MATCHED]
    mine = np.asarray([rows[t] for t in here])[:, columns]
    theirs = np.asarray([source_rows[t] for t in there])[:, columns]

    # [start, column, row], one window per row the stretch could start on
    windows = np.lib.stride_tricks.sliding_window_view(theirs, len(here), axis=0)
    matches = ((np.abs(windows[:, 0] - mine[:, 0]) <= tolerance)
               & (windows[:, 1] == mine[:, 1])).all(axis=1)
    # a stretch the donor has a row missing in is not one it drove
    times = np.asarray(there)
    first, last = times[:len(matches)], times[len(here) - 1:]
    whole = np.abs(last - first - (here[-1] - here[0])) < period / 2
    # replay walks the donor from `source`, so a window starting a row in gives back
    # the time the stretch itself starts from
    return [float(t) - (here[0] - start) for t in first[matches & whole]]


def replay(frames: Iterable[CanFrame], rng: random.Random, donors, *, rows: dict,
           period: float, pgns=MATCHED_PGNS, seconds=SECONDS, spans=None,
           tolerance: float = MAX_DISAGREEMENT) -> tuple | None:
    """Replay one PGN over a random stretch, from a matched moment of one donor.

    `rows` is this log's rows by time. `donors` is a list of (rows, frames_of), each
    donor's rows and what loads its frames, and only the donor picked is loaded. Every
    donor is searched and the moment is picked from all the matches.

    Returns what `random_replay.replay` returns, and None when nothing matches.
    """
    frames = list(frames)
    if not frames or not donors:
        return None
    if spans is None:
        spans = [(frames[0].timestamp, frames[-1].timestamp)]

    length = rng.uniform(*seconds)
    start = time_in(spans, length, rng)
    if start is None:
        return None
    matched = []
    for donor, (donor_rows, _) in enumerate(donors):
        for source in matched_sources(rows, donor_rows, start, start + length,
                                      period=period, tolerance=tolerance):
            matched.append((donor, source))
    if not matched:
        return None
    donor, source = rng.choice(matched)
    source_log = list(donors[donor][1]())

    present = pgns_of(frames) & pgns_of(source_log) & set(pgns)
    if not present:
        return None
    pgn = rng.choice(sorted(present))
    return write_replay(frames, pgn, start, length, source, source_log)
