"""Hold the payload a random moment carried."""

from __future__ import annotations

import random
from typing import Iterable

from attack.replay import repeated_replay
from attack.replay.options import PGNS, SECONDS
from preprocess.frames.can_log_loader import CanFrame


def replay(frames: Iterable[CanFrame], rng: random.Random, pgns=PGNS, seconds=SECONDS,
           *, spans=None) -> tuple | None:
    """Replay one PGN over a random stretch, holding the payload it had at the start.

    Returns what `repeated_replay.replay` returns, with `repeat_seconds` 0 and
    `source` the start.
    """
    return repeated_replay.replay(frames, rng, pgns, seconds, spans=spans,
                                  repeat_seconds=0.0)
