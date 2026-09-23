"""Read logs into one row per tick of a fixed time grid, holding the last value.

    python3 -m assemble.grid data_dir "part_*/*.csv" local_dir repo [--rebuild]

The frames of a log arrive at their own rates. A row every `period` seconds, each
column the last value that signal carried, is what a model and a rule read instead.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os

import numpy as np

from common.cli import arguments
from common.hub_dirs import reuse_or_make
from common.settings import read_settings
from preprocess.features.grid_sample import resample
from preprocess.frames.can_log_loader import load_can_log


def starts_segment(previous, t: float, *, period: float) -> bool:
    """True where a row begins a segment, at the first row or after a gap."""
    return previous is None or t - previous > period * 1.5


def to_arrays(rows, times, segments) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The three lists as arrays, in the dtypes the rest of the pipeline reads."""
    return (
        np.asarray(rows, dtype=np.float32),
        np.asarray(times, dtype=np.float64),    # epoch seconds need the precision
        np.asarray(segments, dtype=np.int32),
    )


def grid_rows(logs, *, period: float, max_hold: float):
    """Read every log into rows, one per tick, with their times and segment ids."""
    arrays, _ = _laid_out(rows_of_each(logs, period=period, max_hold=max_hold),
                          period=period)
    return arrays


def rows_of_each(logs, *, period: float, max_hold: float):
    """Yield each log and the (time, row) pairs it puts on the grid."""
    for path in logs:
        yield path, list(resample(load_can_log(path), period, max_hold))


def _laid_out(logs_rows, *, period: float):
    """The arrays of every log `logs_rows` yields, and how many rows each contributed."""
    rows, times, segments, counts = [], [], [], []
    segment = -1
    for _, log_rows in logs_rows:
        counts.append(len(log_rows))
        previous = None                     # a log starts its own segment
        for t, row in log_rows:
            if starts_segment(previous, t, period=period):
                segment += 1                # a new log, or the grid restarted
            rows.append(row)
            times.append(t)
            segments.append(segment)
            previous = t
    return to_arrays(rows, times, segments), counts


def read_grid(folder):
    """A grid's rows and times, and the logs and row counts its `logs.json` holds.

    The two arrays are mapped rather than read, so taking a part of one costs that part
    rather than the whole grid.
    """
    raw, times = (np.load(os.path.join(folder, f"grid_{n}.npy"), mmap_mode="r")
                  for n in ("raw", "t"))
    with open(os.path.join(folder, "logs.json")) as f:
        kept = json.load(f)
    return raw, times, kept["logs"], kept["rows"]


def rows_of_logs(logs, counts, chosen):
    """True for each row of the grid that came from one of `chosen`, some of `logs`.

    `logs` and `counts` are what a grid's `logs.json` holds, the logs in the order they
    were read and how many rows each contributed.
    """
    ends = np.cumsum(counts)
    chosen = set(chosen)
    from_chosen = np.zeros(int(ends[-1]), bool)
    for log, count, end in zip(logs, counts, ends):
        if log in chosen:
            from_chosen[end - count:end] = True
    return from_chosen


def logs_digest(data_dir, logs):
    """One SHA-256 over each log's path under `data_dir` and its size in bytes."""
    digest = hashlib.sha256()
    for p in logs:
        digest.update(f"{p}\0{os.path.getsize(os.path.join(data_dir, p))}\n".encode())
    return digest.hexdigest()


def write_grid(folder, data_dir, logs, settings):
    """Write the rows of every log, and `logs.json` saying how many each contributed."""
    under = [os.path.join(data_dir, p) for p in logs]
    arrays, counts = _laid_out(rows_of_each(under, period=settings.PERIOD,
                                            max_hold=settings.MAX_HOLD),
                               period=settings.PERIOD)
    for name, array in zip(("raw", "t", "seg"), arrays):
        np.save(os.path.join(folder, f"grid_{name}.npy"), array)
    with open(os.path.join(folder, "logs.json"), "w") as f:
        json.dump({"logs": logs, "rows": counts}, f)
    print(f"{sum(counts)} rows from {len(logs)} logs", flush=True)


def main(data_dir, pattern, local_dir, repo, rebuild=False, settings=None):
    settings = read_settings(settings)
    logs = sorted(os.path.relpath(p, data_dir)
                  for p in glob.glob(os.path.join(data_dir, pattern)))
    if not logs:
        raise SystemExit(f"no log matches {pattern} under {data_dir}")
    inputs = {"logs": logs_digest(data_dir, logs), "count": len(logs),
              "period": settings.PERIOD, "max_hold": settings.MAX_HOLD}
    return reuse_or_make(repo, "grids", inputs, local_dir,
                         lambda folder: write_grid(folder, data_dir, logs, settings),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    main(**arguments(("data_dir", "pattern", "local_dir", "repo"), rebuild=False,
                     settings=None))
