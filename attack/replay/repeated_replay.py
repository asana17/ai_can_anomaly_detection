"""Send the stretch just before a random moment again and again."""

from __future__ import annotations

import random
from typing import Iterable

from attack.replay.options import PGNS, SECONDS, pgns_of, time_in
from attack.replay.replay import write_replay
from preprocess.frames.can_log_loader import CanFrame


def replay(frames: Iterable[CanFrame], rng: random.Random, pgns=PGNS, seconds=SECONDS,
           *, spans=None, repeat_seconds: float | None = None) -> tuple | None:
    """Replay one PGN over a random stretch, repeating its `repeat_seconds` before.

    `repeat_seconds` is drawn from 0 to the length of the stretch when not given. The
    stretch and the `repeat_seconds` before it lie in one of `spans`, a list of
    (start, end) times defaulting to the whole log.

    Returns what `random_replay.replay` returns, with `repeat_seconds` added. `source`
    is `repeat_seconds` before the start.
    """
    frames = list(frames)
    if not frames:
        return None
    present = pgns_of(frames) & set(pgns)
    if not present:
        return None
    if spans is None:
        spans = [(frames[0].timestamp, frames[-1].timestamp)]

    length = rng.uniform(*seconds)
    pgn = rng.choice(sorted(present))
    if repeat_seconds is None:
        repeat_seconds = rng.uniform(0.0, length)
    start = time_in([(first + repeat_seconds, last) for first, last in spans], length,
                    rng)
    if start is None:
        return None
    return write_replay(frames, pgn, start, length, start - repeat_seconds, frames,
                        repeat_seconds=repeat_seconds)
