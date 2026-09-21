"""Count what each detector catches on the attacked test rows.

    python3 -m evaluate.pc.score repo revision attack_sets/<time> local_dir runs_repo revision thresholds/<time> runs_dir [--rebuild]

The models and their thresholds come from a directory `evaluate.calibrate` wrote.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
from dataclasses import replace

import numpy as np
import torch

from assemble.attack_set import fetch_attack_set
from assemble.train_set import read_train_set
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import Settings
from evaluate.counting import (alarms, moved_by, persistent,
                               prepare_scoring_input, touched)
from evaluate.fit import fetch_models
from models.fits import model_from


def fetch_thresholds(directory, runs_dir):
    """The thresholds `directory` holds, and the `meta.json` beside them."""
    folder, meta = read_dir(directory["repo"], directory["path"], runs_dir,
                            directory["revision"])
    with open(os.path.join(folder, "thresholds.json")) as f:
        return json.load(f), meta


def fetch_scale(directory, local_dir):
    """The scale the train set in `directory` fitted, the one its models read rows on."""
    folder, _ = read_dir(directory["repo"], directory["path"], local_dir,
                         directory["revision"], repo_type="dataset")
    _, _, scale = read_train_set(folder)
    return scale


def false_positive_rate(flag, rows_to_score):
    """How often the model flags a row that has no attack on it."""
    clean = rows_to_score["quiet"] & ~rows_to_score["rules"]
    return float((flag & clean).sum() / clean.sum())


def alarming_rows(flag, rows_to_score, need):
    """Raise an alarm where the flag has continued for `need` rows."""
    return persistent(rows_to_score["rules"] | flag, rows_to_score["seg"], need)


def attacks_caught(alarmed, attacks_to_check):
    """Match the alarms against the attacks, and count the attacks they landed in."""
    caught = touched(alarmed, attacks_to_check["injected"])
    return {"found": int(caught.sum()),
            "found_scorable": int((caught & attacks_to_check["scorable"]).sum()),
            "caught": [int(at) for at in np.flatnonzero(caught)]}


def false_alarm_rate(alarmed, rows_to_score):
    """Divide the false alarms by the hours the attack set covers."""
    return float(alarms(alarmed & rows_to_score["quiet"]) / rows_to_score["hours"])


def preprocess_attack_set(directory, local_dir, scale):
    """Scale the rows of a fetched attack set, and give each attack its `moved`."""
    attacked = fetch_attack_set(directory["repo"], directory["revision"],
                                directory["path"], local_dir)
    attacked["rows"] = scale.apply(attacked["raw"])
    for attack in attacked["attacks"]:
        attack["moved"] = moved_by(attack, attacked, scale.std)
    return attacked


def counted(flag, rows_to_score, attacks_to_check, settings):
    """Everything one detector is judged on, at each `HOLD`."""
    kept = {"false_positive_rate": false_positive_rate(flag, rows_to_score)}
    for need in settings.HOLD:
        alarmed = alarming_rows(flag, rows_to_score, need)
        kept[str(need)] = {**attacks_caught(alarmed, attacks_to_check),
                           "alarms_per_hour": false_alarm_rate(alarmed, rows_to_score)}
    return kept


def score_rules(rows_to_score, attacks_to_check, settings):
    """Score the rules on their own, the detector every model is compared against."""
    # the rules are added to every flag, so a flag of nothing leaves the rules alone
    nothing = np.zeros_like(rows_to_score["rules"])
    return {"detector": "rules",
            **counted(nothing, rows_to_score, attacks_to_check, settings)}


def score_models(thresholds, weights, rows_to_score, attacks_to_check, settings):
    """Score each model with the rules, at the threshold calibrate gave it."""
    rows = rows_to_score["rows"]
    kept = []
    for entry in thresholds:
        model = model_from({name: value for name, value in entry.items()
                            if name != "threshold"})    # the rest describes the model
        scores = model.scorer(weights, rows.shape[1])(rows)
        flag = (scores > entry["threshold"]) & rows_to_score["mv"]
        kept.append({**entry,
                     **counted(flag, rows_to_score, attacks_to_check, settings)})
        print(f"{model.name} scored", flush=True)
    return kept


def write_scores(folder, attack_set_directory, thresholds_directory, local_dir,
                 runs_dir, settings):
    """Score the attack set, and write what each detector caught.

    `detection.json` gets one entry per detector. It holds the threshold the detector
    ran at, how often it flagged a row with no attack, and what it caught at each
    `HOLD`. `attacks.json` lists the attacks that were actually injected, where each
    one was and how far it moved a row. What comes back goes into `meta.json`.
    """
    thresholds, thresholds_meta = fetch_thresholds(thresholds_directory, runs_dir)
    models = thresholds_meta["models"]
    weights, _ = fetch_models(models["repo"], models["revision"], models["path"],
                              runs_dir)
    scale = fetch_scale(thresholds_meta["train_set"], local_dir)
    attacked = preprocess_attack_set(attack_set_directory, local_dir, scale)

    settings = replace(settings, MIN_SPEED=attacked["min_speed"])
    rows_to_score, attacks_to_check = prepare_scoring_input(attacked, scale, settings)
    print(f"{int(attacks_to_check['scorable'].sum())} of "
          f"{len(attacked['attacks'])} attacks are scorable, in "
          f"{rows_to_score['hours']:.1f} hours", flush=True)

    with open(os.path.join(folder, "detection.json"), "w") as f:
        json.dump([score_rules(rows_to_score, attacks_to_check, settings),
                   *score_models(thresholds, weights, rows_to_score, attacks_to_check,
                                 settings)], f, indent=2)
    with open(os.path.join(folder, "attacks.json"), "w") as f:
        json.dump([{"log": a["log"], "first": a["first"], "last": a["last"],
                    "moved": a["moved"]} for a in attacked["attacks"]], f, indent=2)

    return {"thresholds": thresholds_directory, "models": models,
            **attacked["dataset"],
            "min_speed": settings.MIN_SPEED, "rows": len(rows_to_score["rows"]),
            "attacks": len(attacked["attacks"]),
            "attacks_scorable": int(attacks_to_check["scorable"].sum()),
            "hours": float(rows_to_score["hours"]),
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "platform": platform.platform()}}


def main(repo, revision, attack_path, local_dir, runs_repo, runs_revision,
         thresholds_path, runs_dir, rebuild=False):
    settings = Settings()
    attack_set_directory = {"repo": repo, "revision": revision, "path": attack_path}
    thresholds_directory = {"repo": runs_repo, "revision": runs_revision,
                            "path": thresholds_path}
    inputs = {"attack_set": attack_path, "thresholds": thresholds_path,
              "moved": settings.MOVED, "hold": settings.HOLD}
    return reuse_or_make(runs_repo, "scores", inputs, runs_dir,
                         lambda folder: write_scores(folder, attack_set_directory,
                                                     thresholds_directory, local_dir,
                                                     runs_dir, settings),
                         rebuild)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("repo", "revision", "attack_path", "local_dir", "runs_repo",
                 "runs_revision", "thresholds_path", "runs_dir"):
        parser.add_argument(name)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    main(args.repo, args.revision, args.attack_path, args.local_dir, args.runs_repo,
         args.runs_revision, args.thresholds_path, args.runs_dir, args.rebuild)
