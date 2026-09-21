"""Give every fitted model the score above which a row counts as an anomaly.

    python3 -m evaluate.calibrate runs_repo revision models/<time> runs_dir local_dir [--rebuild]

The score comes from the calibration rows, which no model was fitted on. A model
reconstructs the rows it was fitted on better than the rest, so a threshold taken from
those would sit too low.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
from dataclasses import replace

import numpy as np
import torch

from assemble.grid import moving
from assemble.train_set import fetch_train_set
from common.hub_dirs import reuse_or_make
from common.settings import Settings
from evaluate.counting import rule_hits
from evaluate.fit import fetch_models
from models.fits import as_dict, models_from


def quantile(scores, share: float):
    """Return the value that `share` of `scores` are above.

    With `share` 0.001, one score in a thousand comes out higher than that value.
    """
    return float(np.percentile(scores, 100 * (1 - share)))


def thresholds_for(models, weights, rows, *, target):
    """Score `rows` with each of `models`, and return each model with its threshold.

    `weights` is what `weights.safetensors` holds, and each model takes its own tensors
    out of it. A model's threshold is the score that `target` of `rows`
    are above.
    """
    kept = []
    for model in models:
        score = model.scorer(weights, rows.shape[1])
        kept.append({**as_dict(model), "threshold": quantile(score(rows), target)})
    return kept


def calibration_rows(train_set, settings):
    """The rows of `train_set` a threshold is taken from, z-scored on its scale.

    Two kinds of calibration row are left out: rows at or below the train set's
    `min_speed`, and rows that a rule in `rules/instant` flags.
    """
    raw, min_speed = train_set["calibration"], train_set["min_speed"]
    # a row a rule already flags says nothing about where to put a model's threshold
    kept = moving(raw, min_speed=min_speed) & ~rule_hits(raw, replace(
        settings, MIN_SPEED=min_speed))
    return train_set["scale"].apply(raw[kept])


def write_thresholds(folder, runs_repo, revision, models_path, runs_dir, local_dir,
                     settings):
    """Write `thresholds.json` into `folder`, and return what its `meta.json` adds."""
    weights, fitted = fetch_models(runs_repo, revision, models_path, runs_dir)
    at = fitted["train_set"]
    train_set = fetch_train_set(at["repo"], at["revision"], at["path"], local_dir)
    rows = calibration_rows(train_set, settings)
    thresholds = thresholds_for(models_from(fitted["inputs"]["models"]), weights, rows,
                                target=settings.TARGET)
    with open(os.path.join(folder, "thresholds.json"), "w") as f:
        json.dump(thresholds, f, indent=2)
    return {"models": {"repo": runs_repo, "revision": revision, "path": models_path},
            **{name: fitted[name] for name in ("train_set", "split", "grid")},
            "min_speed": fitted["min_speed"], "rows": len(rows),
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "platform": platform.platform()}}


def main(runs_repo, revision, models_path, runs_dir, local_dir, rebuild=False):
    settings = Settings()
    inputs = {"models": models_path, "target": settings.TARGET}
    return reuse_or_make(runs_repo, "thresholds", inputs, runs_dir,
                         lambda folder: write_thresholds(folder, runs_repo, revision,
                                                         models_path, runs_dir,
                                                         local_dir, settings),
                         rebuild)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("runs_repo", "revision", "models_path", "runs_dir", "local_dir"):
        parser.add_argument(name)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    main(args.runs_repo, args.revision, args.models_path, args.runs_dir,
         args.local_dir, args.rebuild)
