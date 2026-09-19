"""Read the training, calibration and attacked test rows assemble.dataset built."""

from __future__ import annotations

import json
import os

import numpy as np

from assemble.grid import MAX_HOLD, PERIOD
from assemble.scale import Scale
from assemble.split import split_rows
from preprocess.features.signal_state import SIGNALS

GRID = ("raw", "t", "seg")
ATTACKED = ("rows", "raw", "t", "seg", "label", "wheel")


def grid_with():
    """The settings the grid is built with, as `grid.json` keeps them."""
    return {"signals": SIGNALS, "period": PERIOD, "max_hold": MAX_HOLD}


def built_with(settings):
    """The settings the attack set is built with, as `built.json` keeps them."""
    return {"train": settings.TRAIN, "donors": settings.DONORS,
            "calibration": settings.CALIBRATION, "block": settings.BLOCK,
            "gap": settings.GAP, "seed": settings.SEED, **grid_with()}


def _logs(out_dir, name, expected):
    """The logs `name` lists, after checking it was built with `expected`."""
    kept = json.load(open(os.path.join(out_dir, name)))
    got = {key: kept[key] for key in expected}
    if got != expected:
        raise ValueError(f"{name} in {out_dir} was built with {got}, not {expected}")
    return kept["logs"]


def arrays_from(out_dir, settings):
    """The train and calibration arrays, cut out of the grid by time, on the saved scale."""
    _logs(out_dir, "grid.json", grid_with())
    raw, times, segments = (np.load(os.path.join(out_dir, f"grid_{n}.npy")) for n in GRID)
    train_rows, calibration_rows = split_rows(raw, times, settings.CALIBRATION,
                                              settings.BLOCK, settings.GAP,
                                              settings.MIN_SPEED)
    scale = Scale(*np.load(os.path.join(out_dir, "scale.npy")))
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
    return data


def _stretches(calibration_rows) -> int:
    """How many unbroken runs of calibration rows there are.

    A window a stop interrupts lands in more than one run, so this counts at least as
    many as there are windows.
    """
    return int((calibration_rows
                & ~np.concatenate([[False], calibration_rows[:-1]])).sum())


def attacks_from(out_dir, settings):
    """The attack set, with the train and test logs it was built from."""
    train_logs, test_logs = _logs(out_dir, "built.json", built_with(settings))
    got = {n: np.load(os.path.join(out_dir, f"attacked_{n}.npy")) for n in ATTACKED}
    got["attacks"] = json.load(open(os.path.join(out_dir, "attacked.json")))
    got["train_logs"], got["test_logs"] = train_logs, test_logs
    return got
