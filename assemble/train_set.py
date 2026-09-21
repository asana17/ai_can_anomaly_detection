"""Pick the rows of the non-test logs a model is fitted on.

They are the moving rows more than `GAP` from the test span and from every calibration
block, less the rows a rule hits.

    python3 -m assemble.train_set repo revision calibration_sets/<time> local_dir [--rebuild]
"""

from __future__ import annotations

import json
import os
from dataclasses import replace

import numpy as np

from assemble.calibration_set import read_calibration_blocks, seconds_from
from assemble.grid import read_grid, rows_of_logs
from assemble.split_test_logs import read_log_split
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import Settings
from preprocess.features.moving import moving
from rules.hits import rule_hits


def read_train_set(folder):
    """A train set's train rows."""
    return np.load(os.path.join(folder, "train_rows.npy"))


def fetch_train_set(repo, revision, train_path, local_dir):
    """The rows a train set names, and the directories they came from.

    The train set is read at `revision` of `repo`, and the calibration set, log split
    and grid it names at the commits it names them at.
    """
    folder, meta = read_dir(repo, train_path, local_dir, revision, repo_type="dataset")
    log_split, grid = meta["log_split"], meta["grid"]
    _, log_split_meta = read_dir(log_split["repo"], log_split["path"], local_dir,
                                 log_split["revision"], repo_type="dataset")
    grid_dir, _ = read_dir(grid["repo"], grid["path"], local_dir, grid["revision"],
                           repo_type="dataset")
    raw, _, _, _ = read_grid(grid_dir)
    return {"train": raw[read_train_set(folder)],
            "min_speed": log_split_meta["inputs"]["min_speed"],
            "dataset": {"train_set": {"repo": repo, "revision": revision,
                                      "path": train_path},
                        "calibration_set": meta["calibration_set"],
                        "log_split": log_split, "grid": grid}}


def write_train_set(folder, repo, revision, calibration_path, local_dir, settings):
    """Write which rows train, and return the directories it read for meta.json."""
    calibration_dir, calibration_meta = read_dir(repo, calibration_path, local_dir,
                                                 revision, repo_type="dataset")
    log_split, grid = calibration_meta["log_split"], calibration_meta["grid"]
    log_split_dir, log_split_meta = read_dir(log_split["repo"], log_split["path"],
                                             local_dir, log_split["revision"],
                                             repo_type="dataset")
    grid_dir, _ = read_dir(grid["repo"], grid["path"], local_dir, grid["revision"],
                           repo_type="dataset")
    min_speed = log_split_meta["inputs"]["min_speed"]

    cut = read_log_split(log_split_dir)
    raw, times, logs, counts = read_grid(grid_dir)
    train_rows = (rows_of_logs(logs, counts, cut["non_test"])
                  & moving(raw, min_speed=min_speed)
                  & (seconds_from(times, [[cut["test_start"], cut["test_end"]]])
                     > settings.GAP)
                  & (seconds_from(times, read_calibration_blocks(calibration_dir))
                     > settings.GAP))
    # the model is only asked about the rows no rule hits, so it fits on those alone
    hit = rule_hits(raw[train_rows], replace(settings, MIN_SPEED=min_speed))
    train_rows[train_rows] = ~hit
    print(f"{int(train_rows.sum())} train rows from {len(cut['non_test'])} logs, "
          f"{int(hit.sum())} of {len(hit)} a rule hits dropped", flush=True)

    np.save(os.path.join(folder, "train_rows.npy"), train_rows)
    return {"calibration_set": {"repo": repo, "revision": revision,
                                "path": calibration_path},
            "log_split": log_split, "grid": grid,
            "rule_hits": {"rows": len(hit), "hit": int(hit.sum())}}


def main(repo, revision, calibration_path, local_dir, rebuild=False):
    settings = Settings()
    inputs = {"calibration_set": calibration_path, "gap": settings.GAP}
    return reuse_or_make(repo, "train_sets", inputs, local_dir,
                         lambda folder: write_train_set(folder, repo, revision,
                                                        calibration_path, local_dir,
                                                        settings),
                         rebuild, repo_type="dataset")


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "calibration_path", "local_dir"),
                     rebuild=False))
