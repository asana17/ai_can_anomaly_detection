"""What a replay may be made of: which PGNs, how long, and when."""

from __future__ import annotations

from preprocess.frames.can_id_decompose import decompose_can_id

# The PGNs worth faking, being the ones spn_spec decodes.
PGNS = (61441, 61442, 61443, 61444, 61445, 61449, 65132, 65265, 65266)

# How long an attack runs, in seconds. A log is about a minute, so a longer stretch
# would rarely fit in one, and a grid row is 0.1 s, so the shortest covers 20 rows.
SECONDS = (2.0, 10.0)


def pgns_of(frames) -> set:
    """Which PGNs `frames` carries."""
    return {decompose_can_id(f.can_id).pgn for f in frames}


def time_in(spans, length, rng):
    """A start drawn evenly over the times in `spans` that leave `length` room."""
    room = [(start, end - length) for start, end in spans if end - start > length]
    if not room:
        return None
    start, last = rng.choices(room, weights=[last - start for start, last in room])[0]
    return rng.uniform(start, last)
