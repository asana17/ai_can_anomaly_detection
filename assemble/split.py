"""Split the logs into train and test by time, without shuffling.

    python3 -m assemble.split repo revision grids/<time> local_dir [--rebuild]
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np

from assemble.grid import moving
from common.hub_dirs import download, reuse_or_make
from common.settings import Settings


def split(seconds: dict[str, float], n_splits: int, fold: int):
    """Cut the logs by time into `n_splits` blocks, block `fold` being the test set.

    `seconds` is what seconds_of returns, so the blocks are equal shares of the seconds
    above the minimum speed rather than of the log count. Train is every other block,
    before and after the test one.
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


def _cut(sizes, target: float) -> int:
    """How many logs fit inside `target`."""
    run, i = 0.0, 0
    while i < len(sizes) and run + sizes[i] <= target:
        run += sizes[i]
        i += 1
    return i


def seconds_of(raw, counts, logs, *, min_speed: float, period: float):
    """How many seconds each log spends above `min_speed`, read off the grid's rows.

    `counts` is how many rows each of `logs` contributed, in the same order.
    """
    above = moving(raw, min_speed=min_speed)
    ends = np.cumsum(counts)
    return {log: float(above[end - count:end].sum()) * period
            for log, count, end in zip(logs, counts, ends)}


def span_of(times, counts, logs, wanted):
    """The first and last time of the block `wanted` covers, read off the grid's rows."""
    ends = np.cumsum(counts)
    at = [i for i, log in enumerate(logs) if log in set(wanted)]
    return float(times[ends[at[0]] - counts[at[0]]]), float(times[ends[at[-1]] - 1])


def write_split(folder, repo, revision, grid_path, local_dir, settings):
    """Write `split.json` and `seconds.json` for `FOLD`, cut on the grid `grid_path` of
    `repo` at `revision`, and return the reference to it for `meta.json`."""
    got = download(repo, grid_path, local_dir, repo_type="dataset", revision=revision)
    kept = json.load(open(os.path.join(got, "logs.json")))
    raw, times = (np.load(os.path.join(got, f"grid_{n}.npy")) for n in ("raw", "t"))
    seconds = seconds_of(raw, kept["rows"], kept["logs"],
                         min_speed=settings.MIN_SPEED, period=settings.PERIOD)
    train_logs, test_logs = split(seconds, settings.N_SPLITS, settings.FOLD)
    start, end = span_of(times, kept["rows"], kept["logs"], test_logs)
    print(f"{len(train_logs)} train and {len(test_logs)} test logs, "
          f"{sum(seconds[p] for p in train_logs):.0f}s and "
          f"{sum(seconds[p] for p in test_logs):.0f}s above the minimum speed",
          flush=True)
    with open(os.path.join(folder, "split.json"), "w") as f:
        json.dump({"train": train_logs, "test": test_logs,
                   "test_start": start, "test_end": end}, f)
    with open(os.path.join(folder, "seconds.json"), "w") as f:
        json.dump(seconds, f)
    return {"grid": {"repo": repo, "revision": revision, "path": grid_path}}


def main(repo, revision, grid_path, local_dir, rebuild=False):
    settings = Settings()
    inputs = {"grid": grid_path, "min_speed": settings.MIN_SPEED,
              "n_splits": settings.N_SPLITS, "fold": settings.FOLD}
    return reuse_or_make(repo, "splits", inputs, local_dir,
                         lambda folder: write_split(folder, repo, revision, grid_path,
                                                    local_dir, settings),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("repo", "revision", "grid_path", "local_dir"):
        parser.add_argument(name)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    main(args.repo, args.revision, args.grid_path, args.local_dir, args.rebuild)
