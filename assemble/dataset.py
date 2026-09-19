"""Build the dataset from the logs into `out`, and upload it to Hugging Face.

    python3 -m assemble.dataset "data/part_*/*.csv" out repo branch

Putting the logs on the grid and building the attack set take long, so a step is skipped
when `out` already holds what it would build from the same logs and settings.
"""

from __future__ import annotations

import glob
import json
import os
import random
import sys
import time

import numpy as np
from huggingface_hub import HfApi

from assemble.attack_set import grid_rows_injected
from assemble.split import moving, seconds_above, split, split_rows
from assemble.train_set import grid_rows, scale_for
from common.hf_upload import upload
from common.load_dataset import ATTACKED, GRID, built_with, grid_with
from common.settings import Settings


def seconds_for(logs, out_dir, settings):
    """The seconds each log spends above the minimum speed, measured once and kept.

    A log's own seconds do not depend on which other logs were asked for, so the file
    is a store of every log ever measured rather than one call's answer. A call over a
    different set measures only the logs missing from it. A different `MIN_SPEED`
    measures them all again.
    """
    path = os.path.join(out_dir, "seconds.json")
    store = json.load(open(path)) if os.path.exists(path) else {}
    if store.get("min_speed") != settings.MIN_SPEED:
        store = {"min_speed": settings.MIN_SPEED, "seconds": {}}
    kept = store["seconds"]
    missing = [p for p in logs if p not in kept]
    if missing:
        kept.update(seconds_above(missing, settings.MIN_SPEED))
        json.dump(store, open(path, "w"))
    return {p: kept[p] for p in logs}


def _kept(out_dir, name, shape, files):
    """True when `name` says the files were built as `shape` and all of them are there."""
    path = os.path.join(out_dir, name)
    return (os.path.exists(path) and json.load(open(path)) == shape
            and all(os.path.exists(os.path.join(out_dir, f)) for f in files))


def grid_for(train_logs, out_dir):
    """Put the training logs on the grid in `out_dir`, unless they are there already."""
    shape = {"logs": train_logs, **grid_with()}
    files = [f"grid_{n}.npy" for n in GRID]
    if _kept(out_dir, "grid.json", shape, files):
        return True
    for name, array in zip(files, grid_rows(train_logs)):
        np.save(os.path.join(out_dir, name), array)
    json.dump(shape, open(os.path.join(out_dir, "grid.json"), "w"))
    return False


def fit_scale(out_dir, settings):
    """Fit the scale on the train rows of the grid in `out_dir`, and write it there."""
    raw, times = (np.load(os.path.join(out_dir, f"grid_{n}.npy")) for n in ("raw", "t"))
    train_rows, _ = split_rows(raw, times, settings.CALIBRATION, settings.BLOCK,
                               settings.GAP, settings.MIN_SPEED)
    # the rows PCA is fitted on
    scale = scale_for(raw[train_rows & moving(raw, settings.MIN_SPEED)])
    np.save(os.path.join(out_dir, "scale.npy"), np.stack([scale.mean, scale.std]))
    return scale


def attacks_for(train_logs, test_logs, scale, out_dir, settings):
    """Build the attack set in `out_dir`, unless it is there with the same settings."""
    shape = {"logs": [train_logs, test_logs], **built_with(settings)}
    files = [f"attacked_{n}.npy" for n in ATTACKED] + ["attacked.json"]
    if _kept(out_dir, "built.json", shape, files):
        return True
    donors = settings.DONORS
    got = grid_rows_injected(test_logs, scale, random.Random(settings.SEED),
                             source_logs=train_logs[::max(len(train_logs) // donors, 1)]
                             [:donors])
    for name in ATTACKED:
        np.save(os.path.join(out_dir, f"attacked_{name}.npy"), got[name])
    json.dump(got["attacks"], open(os.path.join(out_dir, "attacked.json"), "w"))
    json.dump(shape, open(os.path.join(out_dir, "built.json"), "w"))
    return False


def main(pattern, out_dir, repo, branch):
    settings = Settings()
    os.makedirs(out_dir, exist_ok=True)
    logs = sorted(glob.glob(pattern))
    seconds = seconds_for(logs, out_dir, settings)
    train_logs, test_logs = split(seconds, settings.TRAIN)
    print(f"{len(train_logs)} train and {len(test_logs)} test logs, "
          f"{sum(seconds[p] for p in train_logs):.0f}s and "
          f"{sum(seconds[p] for p in test_logs):.0f}s above the minimum speed",
          flush=True)

    clock = time.time()
    how = "reused" if grid_for(train_logs, out_dir) else "built"
    print(f"grid {how} in {time.time() - clock:.0f}s", flush=True)

    clock = time.time()
    scale = fit_scale(out_dir, settings)
    kept = attacks_for(train_logs, test_logs, scale, out_dir, settings)
    how = "reused" if kept else "built"
    print(f"attack set {how} in {time.time() - clock:.0f}s", flush=True)

    hub = HfApi()
    hub.create_branch(repo, repo_type="dataset", branch=branch, exist_ok=True)
    commit = upload(repo, out_dir, f"build from {len(logs)} logs", repo_type="dataset",
                    revision=branch, allow_patterns=["*.json", "*.npy"])
    print(f"revision {commit.oid}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
