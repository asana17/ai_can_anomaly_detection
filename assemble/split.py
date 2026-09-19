"""Split the logs by time, without shuffling, and take a calibration set out.

    python3 -m assemble.split repo revision seconds/<time> local_dir [--rebuild]
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Iterable

import numpy as np

from assemble.grid import PERIOD
from common.hub_dirs import download, reuse_or_make
from common.settings import Settings
from preprocess.features.signal_state import SIGNALS
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import load_can_log
from preprocess.frames.frame_decode import decode_frame

CCVS1 = 65265
CCVS1_PERIOD = 0.1      # seconds between wheel speed readings
WHEEL = SIGNALS.index("wheel_speed")


def moving(raw: np.ndarray, min_speed: float) -> np.ndarray:
    """True where a row's wheel speed is above `min_speed`, read off physical values."""
    return raw[:, WHEEL] > min_speed


def seconds_above(logs: Iterable[str], min_speed: float) -> dict[str, float]:
    """How many seconds each log spends above `min_speed`, one number per log.

    Every log is read, which takes about as long as building the arrays from them.
    """
    seconds = {}
    for path in logs:
        readings = 0
        for f in load_can_log(path):
            if decompose_can_id(f.can_id).pgn == CCVS1:
                speed = decode_frame(CCVS1, f.data).get("wheel_speed")
                if speed is not None and speed > min_speed:
                    readings += 1
        seconds[path] = readings * CCVS1_PERIOD
    return seconds


def split(seconds: dict[str, float], n_splits: int, fold: int):
    """Cut the logs by time into `n_splits` blocks, block `fold` being the test set.

    `seconds` is what `seconds_above` returns, so the blocks are equal shares of the
    seconds above the minimum speed rather than of the log count. Train is every other
    block, before and after the test one.
    """
    if not 0 <= fold < n_splits:
        raise ValueError(f"fold {fold} is not one of the {n_splits} blocks")
    ordered = sorted(seconds, key=os.path.basename)     # filename is a timestamp
    sizes = [seconds[p] for p in ordered]
    start = _cut(sizes, sum(sizes) * (fold / n_splits))
    end = len(ordered)                          # the last block runs to the last log
    if fold < n_splits - 1:
        end = _cut(sizes, sum(sizes) * ((fold + 1) / n_splits))
    return ordered[:start] + ordered[end:], ordered[start:end]


def split_rows(raw, times, share: float, block: float, gap: float, min_speed: float):
    """Split the training rows into train and calibration, as two masks over them.

    The rows that set a threshold must be ones the model never saw. Calibration takes
    `share` of the seconds above `min_speed`, in windows of `block` seconds. Train is
    the rest, less the rows within `gap` seconds of a window, which are in neither.
    """
    above = moving(raw, min_speed)
    seconds = (np.cumsum(above) - above) * PERIOD   # above min_speed, before this row
    calibration_rows = above & (seconds % (block / share) < block)
    apart = _apart(times, np.sort(times[calibration_rows]), gap)
    return ~calibration_rows & apart, calibration_rows


def apart_from_test(times, start: float, end: float, gap: float):
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


def _cut(sizes, target: float) -> int:
    """How many logs fit inside `target`."""
    run, i = 0.0, 0
    while i < len(sizes) and run + sizes[i] <= target:
        run += sizes[i]
        i += 1
    return i


def write_split(folder, repo, revision, seconds_path, local_dir, settings):
    """Write `split.json`, the train and test logs of `FOLD`, cut on `seconds_path` of
    `repo` at `revision`, and return the reference to it for `meta.json`."""
    got = download(repo, seconds_path, local_dir, repo_type="dataset", revision=revision)
    seconds = json.load(open(os.path.join(got, "seconds.json")))
    train_logs, test_logs = split(seconds, settings.N_SPLITS, settings.FOLD)
    print(f"{len(train_logs)} train and {len(test_logs)} test logs, "
          f"{sum(seconds[p] for p in train_logs):.0f}s and "
          f"{sum(seconds[p] for p in test_logs):.0f}s above the minimum speed",
          flush=True)
    with open(os.path.join(folder, "split.json"), "w") as f:
        json.dump({"train": train_logs, "test": test_logs}, f)
    return {"seconds": {"repo": repo, "revision": revision, "path": seconds_path}}


def main(repo, revision, seconds_path, local_dir, rebuild=False):
    settings = Settings()
    inputs = {"seconds": seconds_path, "n_splits": settings.N_SPLITS,
              "fold": settings.FOLD}
    return reuse_or_make(repo, "splits", inputs, local_dir,
                         lambda folder: write_split(folder, repo, revision, seconds_path,
                                                    local_dir, settings),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("repo", "revision", "seconds_path", "local_dir"):
        parser.add_argument(name)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    main(args.repo, args.revision, args.seconds_path, args.local_dir, args.rebuild)
