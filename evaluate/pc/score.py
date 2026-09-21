"""Count what each detector catches on the attacked test rows.

    python3 -m evaluate.pc.score repo revision attack_sets/<time> local_dir runs_repo revision thresholds/<time> runs_dir [--rebuild] [--int8]

The models and their thresholds come from a directory `evaluate.calibrate` wrote. With
`--int8` each model is its int8 file, from the directory `deploy.quantize` made from the
same fit at the same `TARGET`.
"""

from __future__ import annotations

import json
import os
import platform
from dataclasses import replace
from functools import partial

import numpy as np
import onnxruntime
import torch

from assemble.attack_set import fetch_attack_set
from assemble.train_set import read_train_set
from common.cli import arguments
from common.hub_dirs import find, read_dir, reuse_or_make
from common.settings import Settings
from evaluate.counting import (alarms, moved_by, persistent,
                               prepare_scoring_input, touched)
from evaluate.fit import fetch_models
from models.fits import model_from
from models.onnx_files import onnx_file_path, onnx_residuals


def fetch_thresholds(directory, runs_dir):
    """The folder of `directory`, its thresholds, and the `meta.json` beside them."""
    folder, meta = read_dir(directory["repo"], directory["path"], runs_dir,
                            directory["revision"])
    with open(os.path.join(folder, "thresholds.json")) as f:
        return folder, json.load(f), meta


def find_quantize(runs_repo, thresholds_meta, runs_dir):
    """The `quantize/` directory made from the fit the thresholds were taken for.

    It is the one quantized at the `TARGET` of the thresholds.
    """
    models_path = thresholds_meta["models"]["path"]
    exported = find(runs_repo, "onnx", {"models": models_path}, runs_dir)
    if exported is None:
        raise ValueError(f"no onnx directory is made from {models_path}")
    target = thresholds_meta["inputs"]["target"]
    quantized = find(runs_repo, "quantize", {"onnx": exported["path"], "target": target},
                     runs_dir)
    if quantized is None:
        raise ValueError(f"no quantize directory is made from {exported['path']} at "
                         f"TARGET {target}")
    return quantized


def torch_scorer(models, runs_dir):
    """What scores rows with a model in torch, on the weights of the fit `models`."""
    weights, _ = fetch_models(models["repo"], models["revision"], models["path"],
                              runs_dir)
    # the scale is fitted on every signal a row holds
    signals = weights["scale.mean"].shape[0]
    return lambda model: model.scorer(weights, signals)


def onnx_scorer(folder, precision):
    """What scores rows with a model in ONNX Runtime, on its `precision` file."""
    return lambda model: partial(onnx_residuals,
                                 onnx_file_path(folder, model, precision))


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


def score_models(thresholds, scorer_of, rows_to_score, attacks_to_check, settings):
    """Score each model with the rules, at the threshold it was given."""
    rows = rows_to_score["rows"]
    kept = []
    for entry in thresholds:
        model = model_from({name: value for name, value in entry.items()
                            if name != "threshold"})    # the rest describes the model
        scores = scorer_of(model)(rows)
        flag = (scores > entry["threshold"]) & rows_to_score["mv"]
        kept.append({**entry,
                     **counted(flag, rows_to_score, attacks_to_check, settings)})
        print(f"{model.name} scored", flush=True)
    return kept


def write_scores(folder, attack_set_directory, thresholds_directory, thresholds,
                 thresholds_meta, onnx_files, local_dir, runs_dir, settings):
    """Score the attack set, and write what each detector caught.

    `detection.json` gets one entry per detector. It holds the threshold the detector
    ran at, how often it flagged a row with no attack, and what it caught at each
    `HOLD`. `attacks.json` lists the attacks that were actually injected, where each
    one was and how far it moved a row. What comes back goes into `meta.json`.

    Each model scores in torch, or with its ONNX file when `onnx_files` names the
    directory and the precision of them.
    """
    if onnx_files is None:
        scorer_of = torch_scorer(thresholds_meta["models"], runs_dir)
        runtime = {"torch": torch.__version__}
    else:
        # the ONNX files come with thresholds of their own
        onnx_folder, thresholds, _ = fetch_thresholds(onnx_files, runs_dir)
        scorer_of = onnx_scorer(onnx_folder, onnx_files["precision"])
        runtime = {"onnxruntime": onnxruntime.__version__}
    scale = fetch_scale(thresholds_meta["train_set"], local_dir)
    attacked = preprocess_attack_set(attack_set_directory, local_dir, scale)

    settings = replace(settings, MIN_SPEED=attacked["min_speed"])
    rows_to_score, attacks_to_check = prepare_scoring_input(attacked, scale, settings)
    print(f"{int(attacks_to_check['scorable'].sum())} of "
          f"{len(attacked['attacks'])} attacks are scorable, in "
          f"{rows_to_score['hours']:.1f} hours", flush=True)

    with open(os.path.join(folder, "detection.json"), "w") as f:
        json.dump([score_rules(rows_to_score, attacks_to_check, settings),
                   *score_models(thresholds, scorer_of, rows_to_score, attacks_to_check,
                                 settings)], f, indent=2)
    with open(os.path.join(folder, "attacks.json"), "w") as f:
        json.dump([{"log": a["log"], "first": a["first"], "last": a["last"],
                    "moved": a["moved"]} for a in attacked["attacks"]], f, indent=2)

    return {"thresholds": thresholds_directory, "onnx_files": onnx_files,
            "models": thresholds_meta["models"],
            **attacked["dataset"],
            "min_speed": settings.MIN_SPEED, "rows": len(rows_to_score["rows"]),
            "attacks": len(attacked["attacks"]),
            "attacks_scorable": int(attacks_to_check["scorable"].sum()),
            "hours": float(rows_to_score["hours"]),
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         **runtime, "platform": platform.platform()}}


def main(repo, revision, attack_path, local_dir, runs_repo, runs_revision,
         thresholds_path, runs_dir, rebuild=False, int8=False):
    settings = Settings()
    attack_set_directory = {"repo": repo, "revision": revision, "path": attack_path}
    thresholds_directory = {"repo": runs_repo, "revision": runs_revision,
                            "path": thresholds_path}
    _, thresholds, thresholds_meta = fetch_thresholds(thresholds_directory, runs_dir)
    onnx_files, onnx_path = None, None
    if int8:
        # the int8 files are in the directory quantize made from the fit
        onnx_files = {**find_quantize(runs_repo, thresholds_meta, runs_dir),
                      "precision": "int8"}
        onnx_path = onnx_files["path"]
    inputs = {"attack_set": attack_path, "thresholds": thresholds_path,
              "onnx_files": onnx_path, "moved": settings.MOVED, "hold": settings.HOLD}
    return reuse_or_make(runs_repo, "scores", inputs, runs_dir,
                         lambda folder: write_scores(folder, attack_set_directory,
                                                     thresholds_directory, thresholds,
                                                     thresholds_meta, onnx_files,
                                                     local_dir, runs_dir, settings),
                         rebuild)


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "attack_path", "local_dir", "runs_repo",
                     "runs_revision", "thresholds_path", "runs_dir"), rebuild=False,
                    int8=False))
