"""Cut the training rows into train and calibration rows, and fit the scale on them.

    python3 -m assemble.train_set repo revision splits/<time> local_dir [--rebuild]
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np

from assemble.grid import moving, read_grid, rows_of_logs
from assemble.scale import Scale, scale_for
from assemble.split import read_split
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import Settings


def split_rows(raw, times, *, share: float, block: float, gap: float, min_speed: float,
               period: float):
    """Split the training rows into train and calibration, as a True per row for each.

    The rows that set a threshold must be ones the model never saw. Calibration takes
    `share` of the seconds above `min_speed`, in windows of `block` seconds. Train is
    the rest, less the rows within `gap` seconds of a window, which are in neither.
    """
    above = moving(raw, min_speed=min_speed)
    seconds = (np.cumsum(above) - above) * period   # above min_speed, before this row
    calibration_rows = above & (seconds % (block / share) < block)
    apart = _apart(times, np.sort(times[calibration_rows]), gap)
    return ~calibration_rows & apart, calibration_rows


def apart_from_test(times, start: float, end: float, *, gap: float):
    """Which rows sit more than `gap` seconds outside the test block, `start` to `end`.

    The rows within `gap` of it go to neither train nor calibration.
    """
    return (times < start - gap) | (times > end + gap)


def _apart(times, windows, gap: float):
    """Which rows sit more than `gap` seconds from every row in `windows`.

    A brake or a gear change can run across the edge of a window, so the rows either
    side of one go to neither set.
    """
    if not len(windows):
        return np.ones(len(times), bool)
    near = np.searchsorted(windows, times)
    before = windows[np.clip(near - 1, 0, len(windows) - 1)]
    after = windows[np.clip(near, 0, len(windows) - 1)]
    return np.minimum(np.abs(times - before), np.abs(times - after)) > gap


def widen_to_grid(training, among_training):
    """A True per training row, widened to a True per row of the whole grid.

    `training` is True for each row of the grid that is a training row, and
    `among_training` holds one value per training row. Every other row comes back False.
    """
    widened = np.zeros(len(training), bool)
    widened[training] = among_training
    return widened


def read_train_set(folder):
    """A train set's train and calibration rows, and the scale fitted on the train ones."""
    train_rows, calibration_rows = (np.load(os.path.join(folder, f"{name}_rows.npy"))
                                    for name in ("train", "calibration"))
    scale = Scale(*np.load(os.path.join(folder, "scale.npy")))
    return train_rows, calibration_rows, scale


def fetch_train_set(repo, revision, train_path, local_dir):
    """The rows a train set names, its scale, and the directories they came from.

    The train set is read at `revision` of `repo`, and the split and grid it names at
    the commits it names them at.
    """
    folder, meta = read_dir(repo, train_path, local_dir, revision, repo_type="dataset")
    split, grid = meta["split"], meta["grid"]
    _, split_meta = read_dir(split["repo"], split["path"], local_dir, split["revision"],
                             repo_type="dataset")
    grid_dir, _ = read_dir(grid["repo"], grid["path"], local_dir, grid["revision"],
                           repo_type="dataset")
    raw, _, _, _ = read_grid(grid_dir)
    train_rows, calibration_rows, scale = read_train_set(folder)
    return {"train": raw[train_rows], "calibration": raw[calibration_rows],
            "scale": scale, "min_speed": split_meta["inputs"]["min_speed"],
            "dataset": {"train_set": {"repo": repo, "revision": revision,
                                      "path": train_path},
                        "split": split, "grid": grid}}


def write_train_set(folder, repo, revision, split_path, local_dir, settings):
    """Write which rows train and calibrate, and the scale, and return the split."""
    split_dir, split_meta = read_dir(repo, split_path, local_dir, revision,
                                     repo_type="dataset")
    grid = split_meta["grid"]
    grid_dir, grid_meta = read_dir(grid["repo"], grid["path"], local_dir,
                                   grid["revision"], repo_type="dataset")
    min_speed = split_meta["inputs"]["min_speed"]
    period = grid_meta["inputs"]["period"]

    cut = read_split(split_dir)
    raw, times, logs, counts = read_grid(grid_dir)
    training = rows_of_logs(logs, counts, cut["train"])

    # the windows are cut on the training rows alone, so the test block never phases them
    train_part, calibration_part = split_rows(raw[training], times[training],
                                              share=settings.CALIBRATION,
                                              block=settings.BLOCK, gap=settings.GAP,
                                              min_speed=min_speed, period=period)
    apart = apart_from_test(times[training], cut["test_start"], cut["test_end"],
                            gap=settings.GAP)
    train_rows = widen_to_grid(training, train_part & apart)
    calibration_rows = widen_to_grid(training, calibration_part & apart)
    scale = scale_for(raw[train_rows & moving(raw, min_speed=min_speed)])
    print(f"{int(training.sum())} rows from {len(cut['train'])} logs, "
          f"{int(train_rows.sum())} train and {int(calibration_rows.sum())} "
          f"calibration", flush=True)

    np.save(os.path.join(folder, "train_rows.npy"), train_rows)
    np.save(os.path.join(folder, "calibration_rows.npy"), calibration_rows)
    np.save(os.path.join(folder, "scale.npy"), np.stack([scale.mean, scale.std]))
    return {"split": {"repo": repo, "revision": revision, "path": split_path},
            "grid": grid}


def main(repo, revision, split_path, local_dir, rebuild=False):
    settings = Settings()
    inputs = {"split": split_path, "calibration": settings.CALIBRATION,
              "block": settings.BLOCK, "gap": settings.GAP}
    return reuse_or_make(repo, "train_sets", inputs, local_dir,
                         lambda folder: write_train_set(folder, repo, revision,
                                                        split_path, local_dir, settings),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("repo", "revision", "split_path", "local_dir"):
        parser.add_argument(name)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    main(args.repo, args.revision, args.split_path, args.local_dir, args.rebuild)
