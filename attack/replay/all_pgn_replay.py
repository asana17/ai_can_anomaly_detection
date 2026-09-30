"""Replay every PGN together from another moment of the same log."""

from __future__ import annotations

import random
from typing import Iterable

from attack.replay.options import PGNS, SECONDS, pgns_of, time_in
from attack.replay.replay import replay as write_payloads
from preprocess.frames.can_log_loader import CanFrame


def replay(frames: Iterable[CanFrame], rng: random.Random, pgns=PGNS, seconds=SECONDS,
           *, spans=None) -> tuple | None:
    """Replay every one of `pgns` the log carries over a random stretch, all from the
    same random moment on.

    The stretch and the moment each lie in one of `spans`, a list of (start, end) times
    defaulting to the whole log.

    Returns the changed frames and a {pgns, start, stop, source} dict, or None when no
    span is long enough, the log carries none of `pgns`, or no payload changed.
    """
    frames = list(frames)
    if not frames:
        return None
    present = sorted(pgns_of(frames) & set(pgns))
    if not present:
        return None
    if spans is None:
        spans = [(frames[0].timestamp, frames[-1].timestamp)]

    length = rng.uniform(*seconds)
    start = time_in(spans, length, rng)
    source = time_in(spans, length, rng)
    if start is None or source is None:
        return None
    hurt = write_payloads(frames, present, start, start + length, source)
    if [f.data for f in hurt] == [f.data for f in frames]:
        return None
    return hurt, dict(pgns=present, start=start, stop=start + length, source=source)
