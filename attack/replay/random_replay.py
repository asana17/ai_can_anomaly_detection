"""Pick a replay at random and apply it."""

from __future__ import annotations

import random
from typing import Iterable

from attack.replay.options import PGNS, SECONDS, pgns_of, time_in
from attack.replay.replay import write_replay
from preprocess.frames.can_log_loader import CanFrame


def replay(frames: Iterable[CanFrame], rng: random.Random,
           source_log: Iterable[CanFrame] | None = None, pgns=PGNS, seconds=SECONDS,
           *, spans=None, source_spans=None) -> tuple | None:
    """Replay one PGN over a random stretch, from a random moment of `source_log`.

    The stretch lies in one of `spans` and the moment in one of `source_spans`, each a
    list of (start, end) times defaulting to the whole log.

    Returns the changed frames and a {pgn, start, stop, source} dict, or None when
    no span is long enough or the replay wrote the bytes that were already there.
    `source` is a time in `source_log`, which is this log unless another is given.
    """
    frames = list(frames)
    source_log = frames if source_log is None else list(source_log)
    if not frames or not source_log:
        return None
    present = pgns_of(frames) & pgns_of(source_log) & set(pgns)
    if not present:
        return None
    if spans is None:
        spans = [(frames[0].timestamp, frames[-1].timestamp)]
    if source_spans is None:
        source_spans = [(source_log[0].timestamp, source_log[-1].timestamp)]

    length = rng.uniform(*seconds)
    pgn = rng.choice(sorted(present))
    start = time_in(spans, length, rng)
    source = time_in(source_spans, length, rng)
    if start is None or source is None:
        return None
    return write_replay(frames, pgn, start, length, source, source_log)


