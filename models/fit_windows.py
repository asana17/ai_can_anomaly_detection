"""Fit every window model on the windows of a train set, and keep the fitted models.

    python3 -m models.fit_windows repo revision train_sets/<time> local_dir runs_repo runs_dir [--models window_models.json] [--rebuild]

The models are the ones `window_models.json` beside this file lists, unless `--models`
names another file. A window is `rows` train rows next to each other in one segment,
oldest first. Every such window is fitted on, one ending at each train row.
"""

from __future__ import annotations

import json
import os
import platform

import numpy as np
import sklearn
import torch
from safetensors.torch import save_file

from assemble.train_set import fetch_train_set
from common.cli import arguments
from common.hub_dirs import reuse_or_make
from models import autoencoder
from models.fit import models_in, scale_for
from models.fits import as_dict
from preprocess.features.moving import moving
from preprocess.features.windows import complete_window_ends, window_rows

MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "window_models.json")


def write_models(folder, models, repo, revision, train_path, local_dir):
    """Fit every model into `folder`, and return what to add to its `meta.json`."""
    train_set = fetch_train_set(repo, revision, train_path, local_dir)
    # a NaN is a value J1939 reserves. No model can fit it, and a rule flags the row
    complete = ~np.isnan(train_set["train"]).any(axis=1)
    scale = scale_for(train_set["train"][complete])
    rows = scale.apply(train_set["train"])
    moved = moving(train_set["train"], min_speed=train_set["min_speed"])

    weights = {"scale.mean": torch.from_numpy(scale.mean),
               "scale.std": torch.from_numpy(scale.std)}
    trained, windows = [], []
    for model in models:
        # a model may fit on one window every `stride` rows, the neighbours being alike
        ends = complete_window_ends(train_set["train"], moved, train_set["seg"],
                                    rows=model.rows, stride=getattr(model, "stride", 1))
        tensors, _, losses = model.fit(window_rows(rows, ends, rows=model.rows))
        weights.update(tensors)
        windows.append(len(ends))
        if losses is not None:
            trained.append({**as_dict(model), "losses": losses})
        print(f"{model.name}, {len(ends)} windows, {len(losses or [])} epochs",
              flush=True)

    save_file(weights, os.path.join(folder, "weights.safetensors"))
    with open(os.path.join(folder, "losses.json"), "w") as f:
        json.dump(trained, f)
    return {**train_set["dataset"], "min_speed": train_set["min_speed"],
            "windows": windows,
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "sklearn": sklearn.__version__,
                         "platform": platform.platform(),
                         "device": autoencoder.device()}}


def main(repo, revision, train_path, local_dir, runs_repo, runs_dir, models=MODELS,
         rebuild=False, dry_run=False):
    fitted = models_in(models)
    return reuse_or_make(runs_repo, "window_models", {"train_set": train_path},
                         {"models": [as_dict(model) for model in fitted]}, runs_dir,
                         lambda folder: write_models(folder, fitted, repo, revision,
                                                     train_path, local_dir),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "train_path", "local_dir", "runs_repo",
                      "runs_dir"), models=MODELS, rebuild=False))
