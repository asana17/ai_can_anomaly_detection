"""Count what each window model adds to the alarm on every tick, on the attacked test
rows.

    python3 -m evaluate.run_window_test_set runs_repo revision test_runs/<time> revision window_thresholds/<time> local_dir runs_dir [--rebuild]

The instant scores, the rule hits and the test set come from a directory
`evaluate.run_test_set` wrote. The window models and their thresholds come from one
`models.calibrate_windows` wrote. The test set's windows are scored with them, as the
calibration set's were, in torch or with the same ONNX files.
"""

from __future__ import annotations

import json
import os
import platform

import numpy as np

from assemble.test_set import fetch_test_set
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import TestRunSettings
from detect.alarm import alarmed_rows, k_of_last_n
from evaluate.count_alarms import (attack_row_mask, attacks_with_a_flagged_row,
                                   count_false_positive_alarms)
from evaluate.run_test_set_common import (attacked_rows_of, attacks_caught,
                                          fetch_thresholds, injected_attacks_of,
                                          threshold_given_to, z_distances_attacks_moved)
from scoring import score, score_windows


def detection_of_one_window_model(scores, threshold, window_scores,
                                    window_threshold, rows_in_window, rows, attacks, n):
    """What the rules and the instant model caught at each k of the last `n` rows, with
    the window model's alarm added.

    The window model flags the last row of each window whose score is above
    `window_threshold`, the row it is judged at. A row where no window ends has NaN,
    which is never above it. The window model alarms where `k` of the last `n` rows
    are flagged, as the rules and the instant model do.
    """
    window_flag = window_scores > window_threshold
    kept = {}
    for k in range(1, n + 1):
        kept[str(k)] = caught_with_the_window_alarm(
            alarmed_rows(scores, threshold, rows.rule_hit, rows.segment, n, k),
            k_of_last_n(window_flag, rows.segment, n, k), rows_in_window, rows, attacks)
    return kept


def caught_with_the_window_alarm(row_alarm, window_alarm, rows_in_window, rows,
                                 attacks):
    """Which attacks the alarm on every tick and the window model's alarm caught, and
    the false positive alarms per hour.

    A window that ends up to `rows_in_window` - 1 rows after an attack still holds its
    rows. The window model's alarm on those rows catches the attack and is not a false
    positive.
    """
    held = [{**a, "last": a["last"] + rows_in_window - 1} for a in attacks.injected]
    caught = (attacks_with_a_flagged_row(row_alarm, attacks.injected)
              | attacks_with_a_flagged_row(window_alarm, held))
    attacked = ((row_alarm & attack_row_mask(attacks.injected, len(row_alarm)))
                | (window_alarm & attack_row_mask(held, len(window_alarm))))
    false_positives = count_false_positive_alarms(row_alarm | window_alarm, attacked)
    return {**attacks_caught(caught, attacks),
            "alarms_per_hour": float(false_positives / rows.hours)}


def detection_of_each_window_model(thresholds, models, scores, window_thresholds,
                           window_models, window_scores, rows, attacks, n):
    """What each instant model caught with the rules and each window model, each at the
    threshold it was given."""
    kept = []
    for model, column in zip(models, scores.T):
        threshold = threshold_given_to(thresholds, model)
        for window_model, window_column in zip(window_models, window_scores.T):
            window_threshold = threshold_given_to(window_thresholds, window_model)
            kept.append({"instant": {**model, "threshold": threshold},
                         "window": {**window_model, "threshold": window_threshold},
                         **detection_of_one_window_model(
                             column, threshold, window_column, window_threshold,
                             window_model["rows"], rows, attacks, n)})
    return kept


def write_window_test_run(folder, test_run_directory, window_thresholds_directory,
                          local_dir, runs_dir, rebuild):
    """Score the test set's windows, count what each window model adds to the alarm on
    every tick of each instant model, and write that.

    `window_detection.json` gets one entry per instant model and window model. It holds
    what they caught at each k of the test run's `n`. What comes back goes into
    `meta.json`. The windows are scored again when `rebuild` is true.
    """
    _, test_run = read_dir(test_run_directory["repo"], test_run_directory["path"],
                           runs_dir, test_run_directory["revision"])
    thresholds, _ = fetch_thresholds(test_run["thresholds"], runs_dir)
    scores, rule_hit, models, _ = score.fetch_scores(test_run["scores"], runs_dir)
    window_thresholds, window_thresholds_meta = fetch_thresholds(
        window_thresholds_directory, runs_dir)
    at = test_run["test_set"]
    fitted = window_thresholds_meta["models"]
    window_onnx_files = window_thresholds_meta["onnx_files"]
    window_scores_directory = score_windows.main(
        at["repo"], at["revision"], at["path"], local_dir, fitted["repo"],
        fitted["revision"], fitted["path"], runs_dir, rebuild=rebuild,
        onnx_files=window_onnx_files and window_onnx_files["path"])
    window_scores, window_models, _ = score_windows.fetch_scores(
        window_scores_directory, runs_dir)
    attacked = fetch_test_set(at["repo"], at["revision"], at["path"], local_dir)
    for attack, moved in zip(attacked["attacks"], z_distances_attacks_moved(
            attacked, test_run["models"], runs_dir)):
        attack["moved"] = moved

    rows = attacked_rows_of(attacked, rule_hit)
    attacks = injected_attacks_of(attacked,
                                  TestRunSettings(MOVED=test_run["inputs"]["moved"]))
    with open(os.path.join(folder, "window_detection.json"), "w") as f:
        json.dump(detection_of_each_window_model(
            thresholds, models, scores, window_thresholds, window_models,
            window_scores, rows, attacks, test_run["inputs"]["n"]), f, indent=2)

    return {"test_run": test_run_directory,
            "window_thresholds": window_thresholds_directory,
            "scores": test_run["scores"], "window_scores": window_scores_directory,
            "models": test_run["models"], "onnx_files": test_run["onnx_files"],
            "window_models": fitted, "window_onnx_files": window_onnx_files,
            **{name: test_run[name] for name in ("test_set", "log_split", "grid",
                                                 "min_speed", "rows", "attacks",
                                                 "attacks_worth_catching", "hours")},
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "platform": platform.platform()}}


def main(runs_repo, test_run_revision, test_run_path, window_thresholds_revision,
         window_thresholds_path, local_dir, runs_dir, rebuild=False, dry_run=False):
    test_run_directory = {"repo": runs_repo, "revision": test_run_revision,
                          "path": test_run_path}
    window_thresholds_directory = {"repo": runs_repo,
                                   "revision": window_thresholds_revision,
                                   "path": window_thresholds_path}
    return reuse_or_make(runs_repo, "window_test_runs",
                         {"test_run": test_run_path,
                          "window_thresholds": window_thresholds_path}, {}, runs_dir,
                         lambda folder: write_window_test_run(
                             folder, test_run_directory, window_thresholds_directory,
                             local_dir, runs_dir, rebuild),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("runs_repo", "test_run_revision", "test_run_path",
                      "window_thresholds_revision", "window_thresholds_path",
                      "local_dir", "runs_dir"), rebuild=False))
