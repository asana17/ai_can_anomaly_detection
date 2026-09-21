"""Give every fitted model the score above which a row counts as an anomaly.

    python3 -m evaluate.calibrate runs_repo revision models/<time> runs_dir local_dir [--rebuild] [--onnx_files <dir> --precision <precision>]

The score comes from the calibration rows, which no model was fitted on. A model
reconstructs the rows it was fitted on better than the rest, so a threshold taken from
those would sit too low. With `--onnx_files` each model is its ONNX file of `precision`
in that directory, made from the same fit.
"""

from __future__ import annotations

import json
import os
import platform
from dataclasses import replace

import numpy as np
import onnxruntime
import torch

from assemble.grid import moving
from assemble.train_set import fetch_train_set
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import Settings
from evaluate.fit import fetch_fitted_models
from models.fits import as_dict, models_from
from models.onnx_files import onnx_scorer
from models.torch_files import torch_scorer
from rules.hits import rule_hits


def quantile(scores, share: float):
    """Return the value that `share` of `scores` are above.

    With `share` 0.001, one score in a thousand comes out higher than that value.
    """
    return float(np.percentile(scores, 100 * (1 - share)))


def thresholds_for(models, scorer_of, rows, *, target):
    """Score `rows` with each of `models`, and return each model with its threshold.

    `scorer_of` gives what scores rows with a model. A model's threshold is the score
    that `target` of `rows` are above.
    """
    kept = []
    for model in models:
        score = scorer_of(model)
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


def write_thresholds(folder, runs_repo, revision, models_path, onnx_directory,
                     onnx_folder, runs_dir, local_dir, settings):
    """Write `thresholds.json` into `folder`, and return what its `meta.json` adds.

    Each model scores in torch, or with its ONNX file when `onnx_directory` names the
    directory and the precision of them, the directory downloaded into `onnx_folder`.
    """
    weights, fitted = fetch_fitted_models(runs_repo, revision, models_path, runs_dir)
    at = fitted["train_set"]
    train_set = fetch_train_set(at["repo"], at["revision"], at["path"], local_dir)
    rows = calibration_rows(train_set, settings)
    if onnx_directory is None:
        scorer_of = torch_scorer(weights)
        runtime = {"torch": torch.__version__}
    else:
        scorer_of = onnx_scorer(onnx_folder, onnx_directory["precision"])
        runtime = {"onnxruntime": onnxruntime.__version__}
    thresholds = thresholds_for(models_from(fitted["inputs"]["models"]), scorer_of,
                                rows, target=settings.TARGET)
    with open(os.path.join(folder, "thresholds.json"), "w") as f:
        json.dump(thresholds, f, indent=2)
    return {"models": {"repo": runs_repo, "revision": revision, "path": models_path},
            "onnx_files": onnx_directory,
            **{name: fitted[name] for name in ("train_set", "split", "grid")},
            "min_speed": fitted["min_speed"], "rows": len(rows),
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         **runtime, "platform": platform.platform()}}


def main(runs_repo, revision, models_path, runs_dir, local_dir, rebuild=False,
         onnx_files=None, precision=None):
    settings = Settings()
    onnx_directory, onnx_folder = None, None
    if onnx_files is not None:
        onnx_directory = {"repo": runs_repo, "revision": revision, "path": onnx_files,
                          "precision": precision}
        onnx_folder, onnx_meta = read_dir(runs_repo, onnx_files, runs_dir, revision)
        made_from = onnx_meta["models"]["path"]
        if made_from != models_path:
            raise ValueError(f"{onnx_files} is made from {made_from}, not {models_path}")
    inputs = {"models": models_path, "target": settings.TARGET, "onnx_files": onnx_files,
              "precision": precision}
    return reuse_or_make(runs_repo, "thresholds", inputs, runs_dir,
                         lambda folder: write_thresholds(folder, runs_repo, revision,
                                                         models_path, onnx_directory,
                                                         onnx_folder, runs_dir,
                                                         local_dir, settings),
                         rebuild)


if __name__ == "__main__":
    main(**arguments(("runs_repo", "revision", "models_path", "runs_dir", "local_dir"),
                    rebuild=False, onnx_files=None, precision=None))
