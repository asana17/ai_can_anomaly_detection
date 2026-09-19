"""Measure each log's seconds above the minimum speed, and upload them to Hugging Face.

    python3 -m assemble.seconds data_dir "part_*/*.csv" local_dir repo [--rebuild]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import time

from assemble.split import seconds_above
from common.git import source
from common.hub_dirs import claim, find, upload, write_meta
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
    found = find(repo, "seconds", inputs, local_dir, repo_type="dataset")
    if found and not rebuild:
        print(f"{found['path']} at {found['revision']} has the same logs and "
              f"MIN_SPEED, pass it on or run again with --rebuild", flush=True)
        return found
    started = time.time()
    path = f"seconds/{time.strftime('%Y%m%d-%H%M%S', time.localtime(started))}"
    folder = claim(repo, path, local_dir, repo_type="dataset")
    code = source()
    os.makedirs(folder)
    write_seconds(folder, data_dir, logs, min_speed)
    write_meta(folder, {"inputs": inputs, **code}, started, time.time())
    made = upload(repo, path, local_dir, f"add {path} from {code['commit'][:7]}",
                  repo_type="dataset")
    print(f"{made['repo']} {made['revision']} {made['path']}", flush=True)
    return made


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data_dir", "pattern", "local_dir", "repo"):
        parser.add_argument(name)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    main(args.data_dir, args.pattern, args.local_dir, args.repo, args.rebuild)
