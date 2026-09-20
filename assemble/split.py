"""Split the logs into train and test by time, without shuffling.

    python3 -m assemble.split repo revision seconds/<time> local_dir [--rebuild]
"""

from __future__ import annotations

import argparse
import json
import os

from common.hub_dirs import download, reuse_or_make
from common.settings import Settings


def split(seconds: dict[str, float], n_splits: int, fold: int):
    """Cut the logs by time into `n_splits` blocks, block `fold` being the test set.

    `seconds` is what seconds_above in assemble.seconds returns, so the blocks are equal
    shares of the seconds above the minimum speed rather than of the log count. Train is
    every other block, before and after the test one.
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
