"""Build the test arrays with attacks in them, and say which rows they cover."""

from __future__ import annotations

import random

import numpy as np

from attack.inject import inject
from assemble.grid import MAX_HOLD, PERIOD, starts_segment, to_arrays
from assemble.split import WHEEL
from preprocess.features.grid_sample import resample
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


def grid_rows_injected(logs, scale, rng: random.Random, source_logs=None) -> dict:
    """Inject one attack into each log, and put the result on train's `scale`.

    Every file contributes its rows whether or not an attack landed, so the set holds
    normal traffic to measure false alarms against. `attacks` says where each one
    sits, as the first and last row it covers, and how far it moved one.
    `source_logs` go to `inject_frames`.
    """
    rows, times, segments, labels, wheels, attacks = [], [], [], [], [], []
    segment = -1
    for _, frames, hurt, span in inject_frames(logs, rng, source_logs):
        clean = dict(resample(frames, PERIOD, MAX_HOLD)) if span else {}
        first = len(rows)
        previous = None
        for t, row in resample(hurt, PERIOD, MAX_HOLD):
            if starts_segment(previous, t):
                segment += 1
            rows.append(row)
            times.append(t)
            segments.append(segment)
            labels.append(t in clean and row != clean[t])
            wheels.append(clean[t][WHEEL] if t in clean else row[WHEEL])
            previous = t
        covered = [i for i in range(first, len(rows)) if labels[i]]
        if span and covered:
            moved = max(np.linalg.norm((np.asarray(rows[i]) - clean[times[i]]) / scale.std)
                        for i in covered)
            attacks.append(dict(span, first=covered[0], last=covered[-1],
                                moved=float(moved)))

    rows, times, segments = to_arrays(rows, times, segments)
    return {
        "rows": scale.apply(rows),
        "raw": rows,
        "t": times,
        "seg": segments,
        "label": np.asarray(labels, dtype=bool),
        "wheel": np.asarray(wheels, dtype=np.float32),
        "attacks": attacks,
    }
