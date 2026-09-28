"""Add a bias to one signal that grows from 0 over the attack, keeping timing."""

from __future__ import annotations

import random
from typing import Iterable

import numpy as np

from attack.replay.options import PGNS, SECONDS, STEPPED, pgns_of, time_in
from attack.spn_encode import set_field
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame
from preprocess.frames.spn_decode import decode
from preprocess.frames.spn_spec import SPEC

# The most the bias reaches, in stds of the signal over the log's own moving frames.
MOST = 2.0


def _values(frames: list, pgn: int, spn, spans) -> list:
    """The values `spn` of `pgn` took within `spans`, leaving out the reserved ones."""
    out = []
    for f in frames:
        if (decompose_can_id(f.can_id).pgn == pgn
                and any(start <= f.timestamp <= end for start, end in spans)):
            value = decode(f.data, spn.field)
            if value is not None:
                out.append(value)
    return out


def ramp(frames: Iterable[CanFrame], rng: random.Random, pgns=PGNS, seconds=SECONDS,
         *, spans=None, most: float = MOST) -> tuple | None:
    """Add a bias to one signal of one PGN over a random stretch, growing in step with
    the time from 0 at the start to its full size at the stop.

    The signal is drawn from those the PGN carries, leaving out `STEPPED`. The full
    size is drawn from 0 to `most` times the signal's std over the log's frames within
    `spans`, and its sign at random. A value is kept within the range J1939 defines for
    it, and a reserved one is left as it is.

    Returns the changed frames and a {pgn, start, stop, signal, bias} dict, or None when
    no span is long enough, the log carries no PGN to fake, or no value changed.
    """
    frames = list(frames)
    if not frames:
        return None
    present = {pgn for pgn in pgns_of(frames) & set(pgns)
               if any(spn.name not in STEPPED for spn in SPEC.get(pgn, []))}
    if not present:
        return None
    if spans is None:
        spans = [(frames[0].timestamp, frames[-1].timestamp)]

    length = rng.uniform(*seconds)
    pgn = rng.choice(sorted(present))
    start = time_in(spans, length, rng)
    if start is None:
        return None
    spn = rng.choice([spn for spn in SPEC[pgn] if spn.name not in STEPPED])
    values = _values(frames, pgn, spn, spans)
    if not values:
        return None
    bias = rng.uniform(0.0, most) * float(np.std(values)) * rng.choice((-1.0, 1.0))

    stop = start + length
    out = []
    for f in frames:
        if (start <= f.timestamp <= stop
                and decompose_can_id(f.can_id).pgn == pgn):
            value = decode(f.data, spn.field)
            if value is not None:
                moved = value + bias * (f.timestamp - start) / length
                moved = min(max(moved, spn.minimum), spn.maximum)
                f = CanFrame(f.timestamp, f.can_id, set_field(f.data, spn.field, moved))
        out.append(f)
    if [f.data for f in out] == [f.data for f in frames]:
        return None
    return out, dict(pgn=pgn, start=start, stop=stop, signal=spn.name, bias=bias)
