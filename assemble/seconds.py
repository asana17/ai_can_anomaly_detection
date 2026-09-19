"""Measure each log's seconds above the minimum speed, and upload them to Hugging Face.

    python3 -m assemble.seconds data_dir "part_*/*.csv" local_dir repo [--rebuild]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os

from assemble.split import seconds_above
from common.hub_dirs import reuse_or_make
from common.settings import Settings


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
