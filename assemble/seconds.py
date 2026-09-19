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

from common.hub_dirs import reuse_or_make
from common.settings import Settings
from preprocess.frames.can_id_decompose import decompose_can_id
from preprocess.frames.can_log_loader import load_can_log
from preprocess.frames.frame_decode import decode_frame

CCVS1 = 65265
CCVS1_PERIOD = 0.1      # seconds between wheel speed readings


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


def logs_digest(data_dir, logs):
    """One SHA-256 over each log's path under `data_dir` and its size in bytes."""
    digest = hashlib.sha256()
    for p in logs:
        digest.update(f"{p}\0{os.path.getsize(os.path.join(data_dir, p))}\n".encode())
    return digest.hexdigest()


def write_seconds(folder, data_dir, logs, min_speed):
    """Write `seconds.json`, each log's seconds above `min_speed`, keyed by `logs`."""
    measured = seconds_above([os.path.join(data_dir, p) for p in logs], min_speed)
    with open(os.path.join(folder, "seconds.json"), "w") as f:
        json.dump({p: measured[os.path.join(data_dir, p)] for p in logs}, f)


def main(data_dir, pattern, local_dir, repo, rebuild=False):
    min_speed = Settings().MIN_SPEED
    logs = sorted(os.path.relpath(p, data_dir)
                  for p in glob.glob(os.path.join(data_dir, pattern)))
    inputs = {"logs": logs_digest(data_dir, logs), "count": len(logs),
              "min_speed": min_speed}
    return reuse_or_make(repo, "seconds", inputs, local_dir,
                         lambda folder: write_seconds(folder, data_dir, logs, min_speed),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data_dir", "pattern", "local_dir", "repo"):
        parser.add_argument(name)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    main(args.data_dir, args.pattern, args.local_dir, args.repo, args.rebuild)
