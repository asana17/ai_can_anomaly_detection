"""Build the training, calibration and attacked test rows from the logs.

What is built is saved in `out`, and read back from there on the next call.
"""

from __future__ import annotations

import json
import os
import random

import numpy as np

from assemble.attack_set import attack_set
from assemble.grid import MAX_HOLD, PERIOD
from assemble.split import moving, seconds_above, split_rows
from assemble.train_set import grid_rows, scale_for
from preprocess.features.signal_state import SIGNALS


def seconds_for(logs, out_dir, settings):
    """The seconds each log spends above the minimum speed, measured once and kept.

    A log's own seconds do not depend on which other logs were asked for, so the file
    is a store of every log ever measured rather than one run's answer. A run over a
    different set measures only the logs missing from it.
    """
    path = os.path.join(out_dir, "seconds.json")
    kept = json.load(open(path)) if os.path.exists(path) else {}
    missing = [p for p in logs if p not in kept]
    if missing:
        kept.update(seconds_above(missing, settings.MIN_SPEED))
        json.dump(kept, open(path, "w"))
    return {p: kept[p] for p in logs}


GRID = ("raw", "t", "seg")
ATTACKED = ("rows", "raw", "t", "seg", "label", "wheel")


def _have(out_dir, names):
    """True once every one of `names` is on disk."""
    return all(os.path.exists(os.path.join(out_dir, n)) for n in names)


def grid_for(train_logs, out_dir):
    """The training logs on the grid, built once and read back on a later run."""
    kept = os.path.join(out_dir, "grid.json")
    shape = {"logs": train_logs, "signals": SIGNALS,
             "period": PERIOD, "max_hold": MAX_HOLD}
    files = [f"grid_{n}.npy" for n in GRID]
    if (os.path.exists(kept) and json.load(open(kept)) == shape
            and _have(out_dir, files)):
        return tuple(np.load(os.path.join(out_dir, f)) for f in files), True
    got = grid_rows(train_logs)
    for name, array in zip(files, got):
        np.save(os.path.join(out_dir, name), array)
    json.dump(shape, open(kept, "w"))
    return got, False


def built_from(train_logs, test_logs, settings):
    """The logs and the settings the attack set was built from."""
    return {"logs": [train_logs, test_logs], "train": settings.TRAIN,
            "donors": settings.DONORS, "calibration": settings.CALIBRATION,
            "block": settings.BLOCK, "gap": settings.GAP, "seed": settings.SEED,
            "signals": SIGNALS, "period": PERIOD, "max_hold": MAX_HOLD}


def arrays_for(train_logs, out_dir, settings):
    """The train and calibration arrays, cut out of the saved grid by time."""
    (raw, times, segments), kept = grid_for(train_logs, out_dir)
    train_rows, calibration_rows = split_rows(raw, times, settings.CALIBRATION,
                                              settings.BLOCK, settings.GAP,
                                              settings.MIN_SPEED)
    above = moving(raw, settings.MIN_SPEED)
    scale = scale_for(raw[train_rows & above])      # the rows PCA is fitted on
    data = {"scale": scale,
            "rows": scale.apply(raw[train_rows]), "raw": raw[train_rows],
            "t": times[train_rows], "seg": segments[train_rows],
            "calibration_rows": scale.apply(raw[calibration_rows]),
            "calibration_raw": raw[calibration_rows],
            "calibration_t": times[calibration_rows],
            "calibration_seg": segments[calibration_rows]}
    print(f"{int(calibration_rows.sum())} calibration rows in "
          f"{_stretches(calibration_rows)} stretches, the gap drops "
          f"{int((~train_rows & ~calibration_rows).sum())} training rows", flush=True)
    return data, kept


def _stretches(calibration_rows) -> int:
    """How many unbroken runs of calibration rows there are.

    A window a stop interrupts lands in more than one run, so this counts at least as
    many as there are windows.
    """
    return int((calibration_rows
                & ~np.concatenate([[False], calibration_rows[:-1]])).sum())


def attacks_for(train_logs, test_logs, scale, out_dir, settings):
    """The attack set, built once and read back on a later run with the same settings."""
    kept = os.path.join(out_dir, "built.json")
    shape = built_from(train_logs, test_logs, settings)
    files = [f"attacked_{n}.npy" for n in ATTACKED] + ["attacked.json"]
    if (os.path.exists(kept) and json.load(open(kept)) == shape
            and _have(out_dir, files)):
        got = {n: np.load(os.path.join(out_dir, f"attacked_{n}.npy"))
               for n in ATTACKED}
        got["attacks"] = json.load(open(os.path.join(out_dir, "attacked.json")))
        return got, True
    donors = settings.DONORS
    got = attack_set(test_logs, scale, random.Random(settings.SEED),
                     source_logs=train_logs[::max(len(train_logs) // donors, 1)]
                     [:donors])
    for name in ATTACKED:
        np.save(os.path.join(out_dir, f"attacked_{name}.npy"), got[name])
    json.dump(got["attacks"], open(os.path.join(out_dir, "attacked.json"), "w"))
    json.dump(shape, open(kept, "w"))
    return got, False
