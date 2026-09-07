"""Pick a replay at random and apply it, for building a labelled test set.

[replay](docs/replay.md) says how to fake an attack. This says which one to fake,
leaving the choice to chance so that the mix of weak and strong attacks is the
data's own rather than one someone picked.
"""

from __future__ import annotations

import random
from typing import Iterable

from attack.replay import replay
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame

# The messages worth faking, being the ones spn_spec decodes.
MESSAGES = (61441, 61442, 61443, 61444, 61445, 61449, 65132, 65265, 65266)

# How long an attack runs. Short enough to leave room in a one minute log, long
# enough to cover several grid rows.
SECONDS = (2.0, 10.0)


def inject(frames: Iterable[CanFrame], rng: random.Random,
           messages=MESSAGES, seconds=SECONDS) -> tuple | None:
    """Replay one message over a random stretch, from a random earlier one.

    Returns the changed frames and a {pgn, start, stop, source} dict, or None when
    the log is too short or the replay wrote the bytes that were already there.
    """
    frames = list(frames)
    present = {decompose_can_id(f.can_id).pgn for f in frames} & set(messages)
    if not present:
        return None
    first, last = frames[0].timestamp, frames[-1].timestamp
    length = rng.uniform(*seconds)
    if last - first < 2 * length:
        return None

    pgn = rng.choice(sorted(present))
    start = rng.uniform(first, last - length)
    source = rng.uniform(first, last - length)
    hurt = replay(frames, [pgn], start, start + length, source)
    if [f.data for f in hurt] == [f.data for f in frames]:
        return None
    return hurt, dict(pgn=pgn, start=start, stop=start + length, source=source)
