"""Build the test arrays with attacks in them, and say which rows they cover."""

from __future__ import annotations

import random

import numpy as np

from attack.inject import inject
from preprocess.features.grid_sample import DEFAULT_MAX_HOLD, DEFAULT_PERIOD, resample
from preprocess.frames.can_log_loader import load_can_log


def attack_set(logs, scale, rng: random.Random, source_logs=None,
               period: float = DEFAULT_PERIOD,
               max_hold: float = DEFAULT_MAX_HOLD) -> dict:
    """Inject one attack into each log, and put the result on train's `scale`.

    Every file contributes its rows whether or not an attack landed, so the set holds
    normal traffic to measure false alarms against. `attacks` says where each one
    sits, as the first and last row it covers, and how far it moved one.
    `source_logs` are the logs the replayed payloads are taken from.
    """
    pool = [list(load_can_log(p)) for p in source_logs] if source_logs else []
    rows, times, segments, labels, attacks = [], [], [], [], []
    segment = -1
    for path in logs:
        frames = list(load_can_log(path))
        made = inject(frames, rng, source_log=rng.choice(pool) if pool else None)
        hurt, span = made if made else (frames, None)
        clean = dict(resample(frames, period, max_hold)) if span else {}
        first = len(rows)
        previous = None
        for t, row in resample(hurt, period, max_hold):
            if previous is None or t - previous > period * 1.5:
                segment += 1
            rows.append(row)
            times.append(t)
            segments.append(segment)
            labels.append(t in clean and row != clean[t])
            previous = t
        covered = [i for i in range(first, len(rows)) if labels[i]]
        if span and covered:
            moved = max(np.linalg.norm((np.asarray(rows[i]) - clean[times[i]]) / scale.std)
                        for i in covered)
            attacks.append(dict(span, first=covered[0], last=covered[-1],
                                moved=float(moved)))

    rows = np.asarray(rows, dtype=np.float32)
    return {
        "rows": scale.apply(rows),
        "raw": rows,
        "t": np.asarray(times, dtype=np.float64),
        "seg": np.asarray(segments, dtype=np.int32),
        "label": np.asarray(labels, dtype=bool),
        "attacks": attacks,
    }
