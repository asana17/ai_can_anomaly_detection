"""What `run_test_set` and `run_window_test_set` both use: the thresholds, the test
set's rows and attacks as a detector is judged over them, and what alarms caught."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import numpy as np

from common.hub_dirs import read_dir
from evaluate.count_alarms import (attack_row_mask, attacks_with_a_flagged_row,
                                   count_false_positive_alarms)
from models.fit import fetch_fitted_models
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


def z_distances_attacks_moved(attacked, models_directory, runs_dir):
    """The z distance each attack of `attacked` moved a row by, in the units of the
    models in `models_directory`."""
    weights, _ = fetch_fitted_models(models_directory["repo"],
                                     models_directory["revision"],
                                     models_directory["path"], runs_dir)
    std = scale_of(weights).std
    return [z_distance_an_attack_moved(attack, attacked, std)
            for attack in attacked["attacks"]]


def attacks_caught(caught, attacks):
    """How many attacks `caught` marks, and which ones they were."""
    return {"found": int(caught.sum()),
            "found_worth_catching": int((caught & attacks.worth_catching).sum()),
            "caught": [int(at) for at in np.flatnonzero(caught)]}


def false_positive_alarms_per_hour(alarmed, rows, attacks):
    """False positive alarms per hour of moving rows with no attack."""
    attacked = attack_row_mask(attacks.injected, len(alarmed))
    return float(count_false_positive_alarms(alarmed, attacked) / rows.hours)


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


def threshold_given_to(thresholds, model):
    """The threshold `calibrate` gave `model`, as `models.json` writes the model down."""
    for entry in thresholds:
        if {name: value for name, value in entry.items() if name != "threshold"} == model:
            return entry["threshold"]
    raise ValueError(f"no threshold for {model}")
