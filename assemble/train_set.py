"""Cut the training rows into train and calibration rows, and fit the scale on them.

    python3 -m assemble.train_set repo revision splits/<time> data_dir local_dir [--rebuild]
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np

from assemble.grid import grid_rows, moving
from assemble.scale import scale_for
from common.hub_dirs import download, reuse_or_make
from common.settings import Settings
from preprocess.frames.can_log_loader import load_can_log


def split_rows(raw, times, *, share: float, block: float, gap: float, min_speed: float,
               period: float):
    """Split the training rows into train and calibration, as two masks over them.

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


def span_of_logs(logs):
    """The first and last frame times of `logs`, read off the first and last of them."""
    first = next(iter(load_can_log(logs[0]))).timestamp
    last = max(f.timestamp for f in load_can_log(logs[-1]))
    return first, last


def write_train_set(folder, repo, revision, split_path, data_dir, local_dir, settings):
    """Write the grid, the two masks and the scale, and return the split for meta.json."""
    got = download(repo, split_path, local_dir, repo_type="dataset", revision=revision)
    logs = json.load(open(os.path.join(got, "split.json")))
    under = {part: [os.path.join(data_dir, p) for p in logs[part]]
             for part in ("train", "test")}
    raw, times, segments = grid_rows(under["train"], period=settings.PERIOD,
                                     max_hold=settings.MAX_HOLD)
    train_rows, calibration_rows = split_rows(raw, times, share=settings.CALIBRATION,
                                              block=settings.BLOCK, gap=settings.GAP,
                                              min_speed=settings.MIN_SPEED,
                                              period=settings.PERIOD)
    apart = apart_from_test(times, *span_of_logs(under["test"]), gap=settings.GAP)
    train_rows, calibration_rows = train_rows & apart, calibration_rows & apart
    scale = scale_for(raw[train_rows & moving(raw, min_speed=settings.MIN_SPEED)])
    print(f"{len(raw)} rows from {len(logs['train'])} logs, "
          f"{int(train_rows.sum())} train and {int(calibration_rows.sum())} "
          f"calibration", flush=True)

    for name, array in zip(("raw", "t", "seg"), (raw, times, segments)):
        np.save(os.path.join(folder, f"grid_{name}.npy"), array)
    np.save(os.path.join(folder, "train_rows.npy"), train_rows)
    np.save(os.path.join(folder, "calibration_rows.npy"), calibration_rows)
    np.save(os.path.join(folder, "scale.npy"), np.stack([scale.mean, scale.std]))
    return {"split": {"repo": repo, "revision": revision, "path": split_path}}


def main(repo, revision, split_path, data_dir, local_dir, rebuild=False):
    settings = Settings()
    inputs = {"split": split_path, "min_speed": settings.MIN_SPEED,
              "calibration": settings.CALIBRATION, "block": settings.BLOCK,
              "gap": settings.GAP}
    return reuse_or_make(repo, "train_sets", inputs, local_dir,
                         lambda folder: write_train_set(folder, repo, revision,
                                                        split_path, data_dir, local_dir,
                                                        settings),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("repo", "revision", "split_path", "data_dir", "local_dir"):
        parser.add_argument(name)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    main(args.repo, args.revision, args.split_path, args.data_dir, args.local_dir,
         args.rebuild)
