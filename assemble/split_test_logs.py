"""Split the logs into test and non-test by time, without shuffling.

    python3 -m assemble.split_test_logs repo revision grids/<time> local_dir [--rebuild]
"""

from __future__ import annotations

import json
import os

import numpy as np

from assemble.grid import read_grid
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import read_settings
from preprocess.features.moving import moving


def split(seconds: dict[str, float], n_splits: int, fold: int):
    """Cut the logs by time into `n_splits` parts, part `fold` being the test logs.

    `seconds` is what seconds_of returns, so the parts are equal shares of the seconds
    above the minimum speed rather than of the log count. Non-test is every other part,
    before and after the test one.
    """
    if not 0 <= fold < n_splits:
        raise ValueError(f"fold {fold} is not one of the {n_splits} parts")
    ordered = sorted(seconds, key=os.path.basename)     # filename is a timestamp
    sizes = [seconds[p] for p in ordered]
    start = _cut(sizes, sum(sizes) * (fold / n_splits))
    end = len(ordered)                          # the last part runs to the last log
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
    """The first and last time of the span `wanted` covers, read off the grid's rows."""
    ends = np.cumsum(counts)
    at = [i for i, log in enumerate(logs) if log in set(wanted)]
    return float(times[ends[at[0]] - counts[at[0]]]), float(times[ends[at[-1]] - 1])


def read_log_split(folder):
    """The test and non-test logs of a `log_splits/<time>/` directory, and the test
    span's first and last time."""
    with open(os.path.join(folder, "log_split.json")) as f:
        return json.load(f)


def write_log_split(folder, repo, revision, grid_path, local_dir, settings):
    """Write `log_split.json` and `seconds.json` for `FOLD`, cut on the grid `grid_path`
    of `repo` at `revision`, and return the reference to it for `meta.json`."""
    got, grid_meta = read_dir(repo, grid_path, local_dir, revision, repo_type="dataset")
    raw, times, logs, counts = read_grid(got)
    seconds = seconds_of(raw, counts, logs, min_speed=settings.MIN_SPEED,
                         period=grid_meta["inputs"]["period"])
    non_test_logs, test_logs = split(seconds, settings.N_SPLITS, settings.FOLD)
    start, end = span_of(times, counts, logs, test_logs)
    print(f"{len(non_test_logs)} non-test and {len(test_logs)} test logs, "
          f"{sum(seconds[p] for p in non_test_logs):.0f}s and "
          f"{sum(seconds[p] for p in test_logs):.0f}s above the minimum speed",
          flush=True)
    with open(os.path.join(folder, "log_split.json"), "w") as f:
        json.dump({"non_test": non_test_logs, "test": test_logs,
                   "test_start": start, "test_end": end}, f)
    with open(os.path.join(folder, "seconds.json"), "w") as f:
        json.dump(seconds, f)
    return {"grid": {"repo": repo, "revision": revision, "path": grid_path}}


def main(repo, revision, grid_path, local_dir, rebuild=False, settings=None):
    settings = read_settings(settings)
    inputs = {"grid": grid_path, "min_speed": settings.MIN_SPEED,
              "n_splits": settings.N_SPLITS, "fold": settings.FOLD}
    return reuse_or_make(repo, "log_splits", inputs, local_dir,
                         lambda folder: write_log_split(folder, repo, revision,
                                                        grid_path, local_dir, settings),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "grid_path", "local_dir"), rebuild=False,
                     settings=None))
