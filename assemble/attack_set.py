"""Build the test arrays with attacks in them, and say which rows they cover."""

from __future__ import annotations

import random

import numpy as np

from attack.inject import inject
from assemble.grid import starts_segment, to_arrays
from preprocess.features.grid_sample import resample
from preprocess.features.signal_state import SIGNALS
from preprocess.frames.can_log_loader import load_can_log


def inject_frames(logs, rng: random.Random, source_logs=None):
    """Inject one attack into each log, and yield its frames before and after it.

    Each item is the path, the frames, the frames with the attack in, and the attack's
    span, or the same frames twice and None when no attack landed. `source_logs` are
    the logs the replayed payloads are taken from.
    """
    pool = [list(load_can_log(p)) for p in source_logs] if source_logs else []
    for path in logs:
        frames = list(load_can_log(path))
        made = inject(frames, rng, source_log=rng.choice(pool) if pool else None)
        hurt, span = made if made else (frames, None)
        yield path, frames, hurt, span


def attacked_log(hurt, span, before, *, period: float, max_hold: float):
    """One attacked log on the grid, and the attack in it, or None.

    `before` is the log's rows by time before the attack, empty when none landed.

    | key | holds |
    | `raw`, `t`, `seg` | the rows, their times, segment ids counting from 0 |
    | `label` | True where the attack changed the row |
    | `wheel` | the wheel speed before the attack |

    The attack is `span` with `first` and `last` added, in this log's rows.
    """
    ticks = list(resample(hurt, period, max_hold))
    times = np.asarray([t for t, _ in ticks], np.float64)
    rows = np.asarray([row for _, row in ticks], np.float32)
    seg = np.cumsum(np.concatenate([[0], np.diff(times) > period * 1.5]))

    known = np.array([t in before for t in times], bool)
    if span is not None and not known.any():
        raise ValueError("no row lines up with the rows before the attack, which are "
                         "on another grid")
    # a grid holds float32, so the rows it did not hold are cast to match the ones it did
    clean = np.asarray([before[t] if seen else row
                        for t, seen, row in zip(times, known, rows)], np.float32)
    label = known & (rows != clean).any(axis=1)

    one = {"raw": rows, "t": times, "seg": seg.astype(np.int32), "label": label,
           "wheel": clean[:, SIGNALS.index("wheel_speed")]}
    covered = np.flatnonzero(label)
    if span is None or not len(covered):
        return one, None
    return one, dict(span, first=int(covered[0]), last=int(covered[-1]))


def _starts(sizes):
    """Where each part begins once the parts are laid end to end."""
    return np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(int)


def grid_rows_injected(injected, rows_before_attack, *, period: float,
                       max_hold: float):
    """Every log of `injected` on the grid, laid end to end.

    A log with no attack contributes its rows too. `rows_before_attack(log)` gives a
    log's rows by time before the attack. Each attack gets its `log`, and its `first`
    and `last` count over all the rows here.
    """
    parts, found = [], []
    for path, _, hurt, span in injected:
        before = rows_before_attack(path) if span is not None else {}
        one, attack = attacked_log(hurt, span, before, period=period,
                                   max_hold=max_hold)
        if not len(one["t"]):
            continue
        parts.append(one)
        found.append(None if attack is None else dict(attack, log=path))

    rows_at = _starts([len(one["t"]) for one in parts])
    segments_at = _starts([int(one["seg"][-1]) + 1 for one in parts])
    joined = {name: np.concatenate([one[name] for one in parts])
              for name in ("raw", "t", "label", "wheel")}
    joined["seg"] = np.concatenate([one["seg"] + at
                                    for one, at in zip(parts, segments_at)])
    attacks = [dict(attack, first=attack["first"] + at, last=attack["last"] + at)
               for attack, at in zip(found, rows_at) if attack is not None]
    return {"attacks": attacks, **joined}
