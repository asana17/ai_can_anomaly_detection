"""Count what each detector catches on the attacked test rows.

    python3 -m evaluate.run_test_set repo revision test_sets/<time> local_dir runs_repo revision thresholds/<time> runs_dir [--rebuild]

The models and their thresholds come from a directory `models.calibrate` wrote. The
test set is scored with them, as the calibration set was.
"""

from __future__ import annotations

import json
import os
import platform

import numpy as np

from assemble.test_set import fetch_test_set
from common.cli import arguments
from common.hub_dirs import reuse_or_make
from common.settings import TestRunSettings
from detect.alarm import alarmed_rows
from evaluate.count_alarms import attacks_with_a_flagged_row
from evaluate.run_test_set_common import (attacked_rows_of, attacks_caught,
                                          false_positive_alarms_per_hour,
                                          fetch_thresholds, injected_attacks_of,
                                          threshold_given_to, z_distances_attacks_moved)
from scoring import score


def false_positive_rate(flag, rows):
    """How often the model flags a moving row that has no attack on it."""
    return float((flag & rows.normal_moving).sum() / rows.normal_moving.sum())


def detection_of_one_detector(scores, threshold, rows, attacks, settings):
    """What one detector caught when k of the last `N` rows raise an alarm, at each k,
    and what it cost in false positives."""
    kept = {"false_positive_rate": false_positive_rate(scores > threshold, rows)}
    for k in range(1, settings.N + 1):
        alarmed = alarmed_rows(scores, threshold, rows.rule_hit, rows.segment,
                               settings.N, k)
        kept[str(k)] = {
            **attacks_caught(attacks_with_a_flagged_row(alarmed, attacks.injected),
                             attacks),
            "alarms_per_hour": false_positive_alarms_per_hour(alarmed, rows, attacks)}
    return kept


def detection_of_the_rules(rows, attacks, settings):
    """What the rules alone caught, the detector every model is compared against."""
    # the rules have no threshold, and no row has a score
    unscored = np.full(len(rows.rule_hit), np.nan)
    return {"detector": "rules",
            **detection_of_one_detector(unscored, np.nan, rows, attacks, settings)}


def detection_of_each_model(thresholds, models, scores, rows, attacks, settings):
    """What each model caught with the rules, at the threshold it was given."""
    kept = []
    for model, column in zip(models, scores.T):
        threshold = threshold_given_to(thresholds, model)
        kept.append({**model, "threshold": threshold,
                     **detection_of_one_detector(column, threshold, rows, attacks,
                                                 settings)})
    return kept


def write_test_run(folder, test_set_directory, thresholds_directory, local_dir,
                   runs_dir, settings, rebuild):
    """Score the test set, count what each detector caught on it, and write that.

    `detection.json` gets one entry per detector. It holds the threshold the detector
    ran at, how often it flagged a row with no attack, and what it caught at each k.
    `attacks.json` lists the attacks that were actually injected, where each one was
    and how far it moved a row. What comes back goes into `meta.json`. The test set
    is scored again when `rebuild` is true.
    """
    thresholds, thresholds_meta = fetch_thresholds(thresholds_directory, runs_dir)
    onnx_files = thresholds_meta["onnx_files"]
    at = thresholds_meta["models"]
    scores_directory = score.main(
        test_set_directory["repo"], test_set_directory["revision"],
        test_set_directory["path"], local_dir, thresholds_directory["repo"],
        thresholds_directory["revision"], at["path"], runs_dir, rebuild=rebuild,
        onnx_files=onnx_files and onnx_files["path"],
        precision=onnx_files and onnx_files["precision"])
    scores, rule_hit, models, _ = score.fetch_scores(scores_directory, runs_dir)
    attacked = fetch_test_set(
        test_set_directory["repo"], test_set_directory["revision"],
        test_set_directory["path"], local_dir)
    for attack, moved in zip(attacked["attacks"],
                             z_distances_attacks_moved(attacked, at, runs_dir)):
        attack["moved"] = moved

    rows = attacked_rows_of(attacked, rule_hit)
    attacks = injected_attacks_of(attacked, settings)
    print(f"{int(attacks.worth_catching.sum())} of "
          f"{len(attacked['attacks'])} attacks are worth catching, in "
          f"{rows.hours:.1f} hours", flush=True)

    with open(os.path.join(folder, "detection.json"), "w") as f:
        json.dump([detection_of_the_rules(rows, attacks, settings),
                   *detection_of_each_model(thresholds, models, scores, rows, attacks,
                                            settings)], f, indent=2)
    with open(os.path.join(folder, "attacks.json"), "w") as f:
        json.dump([{"log": a["log"], "first": a["first"], "last": a["last"],
                    "moved": a["moved"]} for a in attacked["attacks"]], f, indent=2)

    return {"scores": scores_directory, "thresholds": thresholds_directory,
            "models": thresholds_meta["models"], "onnx_files": onnx_files,
            **attacked["dataset"],
            "min_speed": attacked["min_speed"], "rows": len(rule_hit),
            "attacks": len(attacked["attacks"]),
            "attacks_worth_catching": int(attacks.worth_catching.sum()),
            "hours": float(rows.hours),
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "platform": platform.platform()}}


def main(repo, revision, test_path, local_dir, runs_repo, runs_revision,
         thresholds_path, runs_dir, rebuild=False, dry_run=False,
         settings=TestRunSettings()):
    test_set_directory = {"repo": repo, "revision": revision, "path": test_path}
    thresholds_directory = {"repo": runs_repo, "revision": runs_revision,
                            "path": thresholds_path}
    return reuse_or_make(runs_repo, "test_runs",
                         {"test_set": test_path, "thresholds": thresholds_path},
                         {"moved": settings.MOVED, "n": settings.N}, runs_dir,
                         lambda folder: write_test_run(folder, test_set_directory,
                                                       thresholds_directory, local_dir,
                                                       runs_dir, settings, rebuild),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "test_path", "local_dir", "runs_repo",
                     "runs_revision", "thresholds_path", "runs_dir"), rebuild=False))
