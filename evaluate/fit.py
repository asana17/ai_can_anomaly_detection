"""Fit every model on a train set, and keep the fitted models.

    python3 -m evaluate.fit repo revision train_sets/<time> local_dir runs_repo runs_dir [--models models.json] [--rebuild]

The models are the ones `models.json` beside this file lists, the list this
repository's own experiments use, unless `--models` names another file.
`evaluate.calibrate` reads their thresholds off the calibration rows.
"""

from __future__ import annotations

import json
import os
import platform

import numpy as np
import torch
from safetensors.torch import load_file, save_file

from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from assemble.train_set import fetch_train_set
from models.fits import as_dict, models_from

MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models.json")


def fetch_fitted_models(runs_repo, revision, models_path, runs_dir):
    """The weights and `meta.json` of `models_path`, at `revision` of `runs_repo`."""
    folder, meta = read_dir(runs_repo, models_path, runs_dir, revision)
    return load_file(os.path.join(folder, "weights.safetensors")), meta


def models_in(path):
    """The models to fit, read from `path`."""
    print(f"models from {path}", flush=True)
    with open(path) as f:
        return models_from(json.load(f))


def write_models(folder, models, repo, revision, train_path, local_dir):
    """Fit every model into `folder`, and return what to add to its `meta.json`."""
    train_set = fetch_train_set(repo, revision, train_path, local_dir)
    scale, min_speed = train_set["scale"], train_set["min_speed"]
    rows = scale.apply(train_set["train"])
    print(f"{len(rows)} rows to fit on", flush=True)

    weights = {"scale.mean": torch.from_numpy(scale.mean),
               "scale.std": torch.from_numpy(scale.std)}
    trained = []
    for model in models:
        tensors, _, losses = model.fit(rows)
        weights.update(tensors)
        if losses is not None:
            trained.append({**as_dict(model), "losses": losses})
        print(f"{model.name}, {len(losses or [])} epochs", flush=True)

    save_file(weights, os.path.join(folder, "weights.safetensors"))
    with open(os.path.join(folder, "losses.json"), "w") as f:
        json.dump(trained, f)
    return {**train_set["dataset"], "min_speed": min_speed, "rows": len(rows),
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "platform": platform.platform()}}


def main(repo, revision, train_path, local_dir, runs_repo, runs_dir, models=MODELS,
         rebuild=False):
    fitted = models_in(models)
    inputs = {"train_set": train_path, "models": [as_dict(model) for model in fitted]}
    return reuse_or_make(runs_repo, "models", inputs, runs_dir,
                         lambda folder: write_models(folder, fitted, repo, revision,
                                                     train_path, local_dir),
                         rebuild)


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "train_path", "local_dir", "runs_repo",
                      "runs_dir"), models=MODELS, rebuild=False))
