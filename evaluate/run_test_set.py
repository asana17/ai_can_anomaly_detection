"""Count what each detector catches on the attacked test rows.

    python3 -m evaluate.run_test_set repo revision test_sets/<time> local_dir runs_repo revision thresholds/<time> runs_dir [--rebuild]

The models and their thresholds come from a directory `models.calibrate` wrote. The
test set is scored with them, as the calibration set was.
"""

from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass

import numpy as np

from assemble.test_set import fetch_test_set
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import TestRunSettings
from detect.alarm import alarmed_rows
from evaluate.count_alarms import attacks_with_a_flagged_row, count_alarms
from models.fit import fetch_fitted_models
from scoring import score
from models.torch_files import scale_of


def fetch_thresholds(directory, runs_dir):
    """The thresholds in `directory`, and the `meta.json` beside them."""
    folder, meta = read_dir(directory["repo"], directory["path"], runs_dir,
                            directory["revision"])
    with open(os.path.join(folder, "thresholds.json")) as f:
        return json.load(f), meta


def z_distance_an_attack_moved(attack, attacked, std):
    """How far `attack` took a row from the one the bus really produced.

    It is the largest distance over the rows the attack changed, between the attacked
    row and the original, divided by `std`. That is the train set's, so the distance
    is in the units a model reads. `attacked` holds the attacked rows and `before`,
    which gives a log's rows as they were.
    """
    original = attacked["before"](attack["log"])
    changed = [i for i in range(attack["first"], attack["last"] + 1)
               if attacked["label"][i]]
    return float(max(np.linalg.norm((attacked["raw"][i] - original[attacked["t"][i]])
                                    / std) for i in changed))


def false_positive_rate(flag, rows):
    """How often the model flags a moving row that has no attack on it."""
    return float((flag & rows.normal_moving).sum() / rows.normal_moving.sum())


def attacks_caught_by_alarms(alarmed, attacks):
    """How many attacks an alarm fell inside, and which ones they were."""
    caught = attacks_with_a_flagged_row(alarmed, attacks.injected)
    return {"found": int(caught.sum()),
            "found_worth_catching": int((caught & attacks.worth_catching).sum()),
            "caught": [int(at) for at in np.flatnonzero(caught)]}


def false_alarms_per_hour(alarmed, rows):
    """The alarms raised on rows with no attack, over the hours they cover."""
    return float(count_alarms(alarmed & rows.normal_moving) / rows.hours)


@dataclass
class AttackedRows:
    """The rows of a test set, as a detector is judged over them.

    `normal_moving` marks the rows above `MIN_SPEED` that carry no attack, `rule_hit`
    where an instant rule fires, `segment` the segment ids, and `hours` how long the
    `normal_moving` rows run for.
    """
    normal_moving: np.ndarray
    rule_hit: np.ndarray
    segment: np.ndarray
    hours: float


@dataclass
class InjectedAttacks:
    """The attacks in a test set, as a detector is judged against them.

    `injected` is every attack that was injected. `worth_catching` marks those that
    reach a row whose speed before the attack was above `MIN_SPEED` and moved a row by
    at least `MOVED`. The rest are left out of the rate, since no detector could be
    asked to catch them.
    """
    injected: list
    worth_catching: np.ndarray


def attacked_rows_of(attacked, rule_hit):
    """The test set's rows, with the normal moving ones marked and their hours worked
    out."""
    normal_moving = (attacked["wheel"] > attacked["min_speed"]) & ~attacked["label"]
    return AttackedRows(normal_moving=normal_moving, rule_hit=rule_hit,
                        segment=attacked["seg"],
                        hours=float(normal_moving.sum() * attacked["period"] / 3600))


def injected_attacks_of(attacked, settings):
    """The test set's attacks, with the ones worth catching marked."""
    # the speed before the attack, so an attack faking 0 km/h is still worth catching
    truth = attacked["wheel"] > attacked["min_speed"]
    moved = np.array([a["moved"] for a in attacked["attacks"]])
    return InjectedAttacks(
        injected=attacked["attacks"],
        worth_catching=(attacks_with_a_flagged_row(truth, attacked["attacks"])
                        & (moved >= settings.MOVED)))


def detection_of_one_detector(scores, threshold, rows, attacks, settings):
    """What one detector caught, at each `HOLD`, and what it cost in false positives."""
    kept = {"false_positive_rate": false_positive_rate(scores > threshold, rows)}
    for need in settings.HOLD:
        alarmed = alarmed_rows(scores, threshold, rows.rule_hit, rows.segment, need)
        kept[str(need)] = {**attacks_caught_by_alarms(alarmed, attacks),
                           "alarms_per_hour": false_alarms_per_hour(alarmed, rows)}
    return kept


def detection_of_the_rules(rows, attacks, settings):
    """What the rules alone caught, the detector every model is compared against."""
    # the rules have no threshold, and no row has a score
    unscored = np.full(len(rows.rule_hit), np.nan)
    return {"detector": "rules",
            **detection_of_one_detector(unscored, np.nan, rows, attacks, settings)}


def threshold_given_to(thresholds, model):
    """The threshold `calibrate` gave `model`, as `models.json` writes the model down."""
    for entry in thresholds:
        if {name: value for name, value in entry.items() if name != "threshold"} == model:
            return entry["threshold"]
    raise ValueError(f"no threshold for {model}")


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
                   runs_dir, settings):
    """Score the test set, count what each detector caught on it, and write that.

    `detection.json` gets one entry per detector. It holds the threshold the detector
    ran at, how often it flagged a row with no attack, and what it caught at each
    `HOLD`. `attacks.json` lists the attacks that were actually injected, where each
    one was and how far it moved a row. What comes back goes into `meta.json`.
    """
    thresholds, thresholds_meta = fetch_thresholds(thresholds_directory, runs_dir)
    onnx_files = thresholds_meta["onnx_files"]
    at = thresholds_meta["models"]
    scores_directory = score.main(
        test_set_directory["repo"], test_set_directory["revision"],
        test_set_directory["path"], local_dir, thresholds_directory["repo"],
        thresholds_directory["revision"], at["path"], runs_dir,
        onnx_files=onnx_files and onnx_files["path"],
        precision=onnx_files and onnx_files["precision"])
    scores, rule_hit, models, _ = score.fetch_scores(scores_directory, runs_dir)
    weights, _ = fetch_fitted_models(at["repo"], at["revision"], at["path"], runs_dir)
    std = scale_of(weights).std
    attacked = fetch_test_set(
        test_set_directory["repo"], test_set_directory["revision"],
        test_set_directory["path"], local_dir)
    for attack in attacked["attacks"]:
        attack["moved"] = z_distance_an_attack_moved(attack, attacked, std)

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
                         {"moved": settings.MOVED, "hold": settings.HOLD}, runs_dir,
                         lambda folder: write_test_run(folder, test_set_directory,
                                                       thresholds_directory, local_dir,
                                                       runs_dir, settings),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "test_path", "local_dir", "runs_repo",
                     "runs_revision", "thresholds_path", "runs_dir"), rebuild=False))
