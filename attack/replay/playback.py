"""Overwrite one signal with the values it took at another moment of the same log."""

from __future__ import annotations

import random
from typing import Iterable

from attack.replay.options import PGNS, SECONDS, STEPPED, pgns_of, time_in
from attack.replay.replay import _by_pgn, _nearest
from attack.spn_encode import set_field
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame
from preprocess.frames.spn_decode import decode
from preprocess.frames.spn_spec import SPEC


def replay(frames: Iterable[CanFrame], rng: random.Random, pgns=PGNS, seconds=SECONDS,
           *, spans=None) -> tuple | None:
    """Overwrite one signal of one PGN over a random stretch with the values it took
    from a random moment on, the other signals of the PGN keeping theirs.

    The stretch and the moment each lie in one of `spans`, a list of (start, end) times
    defaulting to the whole log. The signal is drawn from those the PGN carries,
    leaving out `STEPPED`. A reserved value, in the frame or in the one copied from, is
    left as it is.

    Returns the changed frames and a {pgn, start, stop, source, signal} dict, or None
    when no span is long enough, the log carries no PGN to fake, or no value changed.
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
    source = time_in(spans, length, rng)
    if start is None or source is None:
        return None
    spn = rng.choice([spn for spn in SPEC[pgn] if spn.name not in STEPPED])

    times, data = _by_pgn(frames, {pgn})[pgn]
    stop = start + length
    out = []
    for f in frames:
        if start <= f.timestamp <= stop and decompose_can_id(f.can_id).pgn == pgn:
            copied = decode(_nearest(times, data, source + (f.timestamp - start)),
                            spn.field)
            if copied is not None and decode(f.data, spn.field) is not None:
                f = CanFrame(f.timestamp, f.can_id,
                             set_field(f.data, spn.field, copied))
        out.append(f)
    if [f.data for f in out] == [f.data for f in frames]:
        return None
    return out, dict(pgn=pgn, start=start, stop=stop, source=source, signal=spn.name)
