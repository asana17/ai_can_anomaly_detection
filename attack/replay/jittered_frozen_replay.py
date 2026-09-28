"""Hold the payload a random moment carried, jittered as the log itself jitters."""

from __future__ import annotations

import random
from typing import Iterable

from attack.replay import frozen_replay
from attack.replay.options import PGNS, SECONDS
from attack.spn_encode import set_field
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import CanFrame
from preprocess.frames.spn_decode import extract_le
from preprocess.frames.spn_spec import SPEC


def _reserved(field) -> int:
    """The lowest raw value J1939 reserves for `field`."""
    return 0xFE << max(field.length - 8, 0)


def steps(frames: list, pgn: int, spans) -> list:
    """For each signal `pgn` carries, the raw steps from one frame of it to the next,
    within each of `spans`. A step to or from a reserved value is left out."""
    out = [[] for _ in SPEC.get(pgn, [])]
    for start, end in spans:
        mine = [f.data for f in frames if start <= f.timestamp <= end
                and decompose_can_id(f.can_id).pgn == pgn]
        for before, after in zip(mine, mine[1:]):
            for taken, spn in zip(out, SPEC[pgn]):
                a = extract_le(before, spn.field.start_bit, spn.field.length)
                b = extract_le(after, spn.field.start_bit, spn.field.length)
                if max(a, b) < _reserved(spn.field):
                    taken.append(b - a)
    return out


def jitter(data: bytes, pgn: int, steps_of: list, rng: random.Random) -> bytes:
    """`data` with a step drawn from `steps_of` added to the raw value of each signal
    `pgn` carries.

    A signal with no step to draw from, one J1939 reserves the value of, or one the
    step would take out of its bits or into the reserved values, is left as it is.
    """
    for spn, taken in zip(SPEC.get(pgn, []), steps_of):
        field = spn.field
        held = extract_le(data, field.start_bit, field.length)
        if not taken or held >= _reserved(field):
            continue
        raw = held + rng.choice(taken)
        if 0 <= raw < _reserved(field):
            data = set_field(data, field, raw * field.scale + field.offset)
    return data


def replay(frames: Iterable[CanFrame], rng: random.Random, pgns=PGNS, seconds=SECONDS,
           *, spans=None) -> tuple | None:
    """Replay one PGN over a random stretch, holding the payload it had at the start
    and jittering each frame of it by a step the log itself took.

    The steps are taken within `spans`, the whole log when not given. Returns what
    `frozen_replay.replay` returns.
    """
    frames = list(frames)
    made = frozen_replay.replay(frames, rng, pgns, seconds, spans=spans)
    if made is None:
        return None
    hurt, found = made
    if spans is None:
        spans = [(frames[0].timestamp, frames[-1].timestamp)]
    steps_of = steps(frames, found["pgn"], spans)
    out = []
    for f in hurt:
        if (found["start"] <= f.timestamp <= found["stop"]
                and decompose_can_id(f.can_id).pgn == found["pgn"]):
            f = CanFrame(f.timestamp, f.can_id,
                         jitter(f.data, found["pgn"], steps_of, rng))
        out.append(f)
    return out, found
