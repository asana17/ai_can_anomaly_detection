"""Measure each log's seconds above the minimum speed, and upload them to Hugging Face.

    python3 -m assemble.seconds data_dir "part_*/*.csv" local_dir repo [--rebuild]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
from typing import Iterable

from assemble.grid import grid_rows, moving
from common.hub_dirs import reuse_or_make
from common.settings import Settings
from preprocess.features.signal_state import SIGNALS


def seconds_above(logs: Iterable[str], min_speed: float, period: float,
                  max_hold: float) -> dict[str, float]:
    """How many seconds each log spends above `min_speed`, one number per log.

    They are the log's rows on the grid that are moving, so a split sized on them
    counts the same rows train_set and attack_set score.
    """
    seconds = {}
    for path in logs:
        raw, _, _ = grid_rows([path], period, max_hold)
        # a log with no row comes back 1-d
        above = moving(raw.reshape(-1, len(SIGNALS)), min_speed)
        seconds[path] = float(above.sum()) * period
    return seconds


def logs_digest(data_dir, logs):
    """One SHA-256 over each log's path under `data_dir` and its size in bytes."""
    digest = hashlib.sha256()
    for p in logs:
        digest.update(f"{p}\0{os.path.getsize(os.path.join(data_dir, p))}\n".encode())
    return digest.hexdigest()


def write_seconds(folder, data_dir, logs, settings):
    """Write `seconds.json`, each log's seconds above `MIN_SPEED`, keyed by `logs`."""
    measured = seconds_above([os.path.join(data_dir, p) for p in logs],
                             settings.MIN_SPEED, settings.PERIOD, settings.MAX_HOLD)
    with open(os.path.join(folder, "seconds.json"), "w") as f:
        json.dump({p: measured[os.path.join(data_dir, p)] for p in logs}, f)


def main(data_dir, pattern, local_dir, repo, rebuild=False):
    settings = Settings()
    logs = sorted(os.path.relpath(p, data_dir)
                  for p in glob.glob(os.path.join(data_dir, pattern)))
    inputs = {"logs": logs_digest(data_dir, logs), "count": len(logs),
              "min_speed": settings.MIN_SPEED, "period": settings.PERIOD,
              "max_hold": settings.MAX_HOLD}
    return reuse_or_make(repo, "seconds", inputs, local_dir,
                         lambda folder: write_seconds(folder, data_dir, logs, settings),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data_dir", "pattern", "local_dir", "repo"):
        parser.add_argument(name)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    main(args.data_dir, args.pattern, args.local_dir, args.repo, args.rebuild)
