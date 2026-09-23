"""Cut the non-test logs' time into calibration blocks, and pick the rows in them.

The rows are the moving rows inside a block more than `GAP` from the test span.

    python3 -m assemble.calibration_set repo revision log_splits/<time> local_dir [--rebuild]
"""

from __future__ import annotations

import json
import os

import numpy as np

from assemble.grid import read_grid, rows_of_logs
from assemble.split_test_logs import read_log_split
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import read_settings
from preprocess.features.moving import moving


def calibration_blocks(raw, times, *, share: float, block: float, min_speed: float,
                       period: float):
    """The first and last time of each calibration block over the non-test rows.

    Calibration takes `share` of the seconds above `min_speed`, in blocks of `block`
    seconds.
    """
    above = moving(raw, min_speed=min_speed)
    seconds = (np.cumsum(above) - above) * period   # above min_speed, before this row
    calibration_rows = above & (seconds % (block / share) < block)
    number = (seconds // (block / share))[calibration_rows]
    at = times[calibration_rows]
    first = np.flatnonzero(np.diff(number, prepend=-1) != 0)
    last = np.append(first[1:] - 1, len(number) - 1)
    return [[float(at[f]), float(at[t])] for f, t in zip(first, last)]


def seconds_from(times, spans):
    """How many seconds each of `times` lies from the nearest of `spans`, 0 inside one.

    `spans` are `[first, last]` pairs in time order that do not overlap.
    """
    if not len(spans):
        return np.full(len(times), np.inf)
    starts, ends = np.asarray(spans, dtype=np.float64).T
    at = np.searchsorted(starts, times, side="right")   # spans starting at or before
    before = np.where(at > 0, times - ends[np.maximum(at - 1, 0)], np.inf)
    after = np.where(at < len(starts), starts[np.minimum(at, len(starts) - 1)] - times,
                     np.inf)
    return np.maximum(np.minimum(before, after), 0.0)


def read_calibration_set(folder):
    """A calibration set's calibration rows."""
    return np.load(os.path.join(folder, "calibration_rows.npy"))


def read_calibration_blocks(folder):
    """A calibration set's blocks, as `[first, last]` times."""
    with open(os.path.join(folder, "blocks.json")) as f:
        return json.load(f)


def fetch_calibration_set(repo, revision, calibration_path, local_dir):
    """The rows a calibration set names, and the directories they came from.

    The calibration set is read at `revision` of `repo`, and the log split and grid it
    names at the commits it names them at.
    """
    folder, meta = read_dir(repo, calibration_path, local_dir, revision,
                            repo_type="dataset")
    log_split, grid = meta["log_split"], meta["grid"]
    _, log_split_meta = read_dir(log_split["repo"], log_split["path"], local_dir,
                                 log_split["revision"], repo_type="dataset")
    grid_dir, _ = read_dir(grid["repo"], grid["path"], local_dir, grid["revision"],
                           repo_type="dataset")
    raw, _, _, _ = read_grid(grid_dir)
    return {"calibration": raw[read_calibration_set(folder)],
            "min_speed": log_split_meta["inputs"]["min_speed"],
            "dataset": {"calibration_set": {"repo": repo, "revision": revision,
                                            "path": calibration_path},
                        "log_split": log_split, "grid": grid}}


def write_calibration_set(folder, repo, revision, log_split_path, local_dir, settings):
    """Write the blocks and which rows calibrate, and return the log split for meta.json.

    The blocks are cut over the non-test rows alone, so the test span never phases them.
    """
    log_split_dir, log_split_meta = read_dir(repo, log_split_path, local_dir, revision,
                                             repo_type="dataset")
    grid = log_split_meta["grid"]
    grid_dir, grid_meta = read_dir(grid["repo"], grid["path"], local_dir,
                                   grid["revision"], repo_type="dataset")
    min_speed = log_split_meta["inputs"]["min_speed"]

    cut = read_log_split(log_split_dir)
    raw, times, logs, counts = read_grid(grid_dir)
    non_test = rows_of_logs(logs, counts, cut["non_test"])
    blocks = calibration_blocks(raw[non_test], times[non_test],
                                share=settings.CALIBRATION, block=settings.BLOCK,
                                min_speed=min_speed, period=grid_meta["inputs"]["period"])
    calibration_rows = (non_test & moving(raw, min_speed=min_speed)
                        & (seconds_from(times, blocks) == 0)
                        & (seconds_from(times, [[cut["test_start"], cut["test_end"]]])
                           > settings.GAP))
    print(f"{int(calibration_rows.sum())} calibration rows in {len(blocks)} blocks",
          flush=True)

    with open(os.path.join(folder, "blocks.json"), "w") as f:
        json.dump(blocks, f)
    np.save(os.path.join(folder, "calibration_rows.npy"), calibration_rows)
    return {"log_split": {"repo": repo, "revision": revision, "path": log_split_path},
            "grid": grid}


def main(repo, revision, log_split_path, local_dir, rebuild=False, settings=None):
    settings = read_settings(settings)
    inputs = {"log_split": log_split_path, "calibration": settings.CALIBRATION,
              "block": settings.BLOCK, "gap": settings.GAP}
    return reuse_or_make(repo, "calibration_sets", inputs, local_dir,
                         lambda folder: write_calibration_set(folder, repo, revision,
                                                              log_split_path, local_dir,
                                                              settings),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "log_split_path", "local_dir"), rebuild=False,
                     settings=None))
