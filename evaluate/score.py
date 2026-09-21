"""Score every row of a set with each fitted model, and flag the rows a rule hits.

    python3 -m evaluate.score repo revision <set> local_dir runs_repo revision models/<time> runs_dir [--rebuild] [--onnx_files <dir> --precision <precision>]

`<set>` is `calibration_sets/<time>` or `test_sets/<time>`. With `--onnx_files` each
model is its ONNX file of `precision` in that directory, made from the same fit.
"""

from __future__ import annotations

import json
import os
import platform
from dataclasses import replace

import numpy as np
import onnxruntime
import torch

from assemble.calibration_set import fetch_calibration_set
from assemble.test_set import fetch_test_set
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import Settings
from evaluate.fit import fetch_fitted_models
from models.fits import as_dict, models_from
from models.onnx_files import onnx_scorer
from models.torch_files import scale_of, torch_scorer
from preprocess.features.moving import moving
from rules.hits import rule_hits


def fetch_set_rows(directory, local_dir):
    """The rows of the set `directory` names, its `min_speed`, and where they came from."""
    at = (directory["repo"], directory["revision"], directory["path"], local_dir)
    if directory["path"].startswith("test_sets/"):
        got = fetch_test_set(*at)
        return got["raw"], got["min_speed"], got["dataset"]
    got = fetch_calibration_set(*at)
    return got["calibration"], got["min_speed"], got["dataset"]


def scores_of(models, scorer_of, rows, scored):
    """One column per model of its score on each of `rows`, NaN where not `scored`."""
    scores = np.full((len(rows), len(models)), np.nan, np.float32)
    for column, model in enumerate(models):
        scores[scored, column] = scorer_of(model)(rows[scored])
        print(f"{model.name} scored", flush=True)
    return scores


def write_scores(folder, set_directory, models_directory, onnx_directory, onnx_folder,
                 local_dir, runs_dir, settings):
    """Write each row's scores and rule hits into `folder`, and return what `meta.json`
    adds.

    A model scores the moving rows. Each model scores in torch, or with its
    ONNX file when `onnx_directory` names the directory and the precision of them, the
    directory downloaded into `onnx_folder`.
    """
    weights, fitted = fetch_fitted_models(models_directory["repo"],
                                          models_directory["revision"],
                                          models_directory["path"], runs_dir)
    if onnx_directory is None:
        scorer_of = torch_scorer(weights)
        runtime = {"torch": torch.__version__}
    else:
        scorer_of = onnx_scorer(onnx_folder, onnx_directory["precision"])
        runtime = {"onnxruntime": onnxruntime.__version__}
    raw, min_speed, dataset = fetch_set_rows(set_directory, local_dir)
    mv = moving(raw, min_speed=min_speed)
    hits = rule_hits(raw, replace(settings, MIN_SPEED=min_speed)) & mv
    models = models_from(fitted["inputs"]["models"])
    scores = scores_of(models, scorer_of, scale_of(weights).apply(raw), mv)

    np.save(os.path.join(folder, "scores.npy"), scores)
    np.save(os.path.join(folder, "rule_hits.npy"), hits)
    with open(os.path.join(folder, "models.json"), "w") as f:
        json.dump([as_dict(model) for model in models], f, indent=2)
    return {"models": models_directory, "onnx_files": onnx_directory, **dataset,
            "min_speed": min_speed, "rows": len(raw), "scored": int(mv.sum()),
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         **runtime, "platform": platform.platform()}}


def fetch_scores(directory, runs_dir):
    """The scores and rule hits in `directory`, the models of the scores' columns, and
    its `meta.json`."""
    folder, meta = read_dir(directory["repo"], directory["path"], runs_dir,
                            directory["revision"])
    with open(os.path.join(folder, "models.json")) as f:
        models = json.load(f)
    return (np.load(os.path.join(folder, "scores.npy")),
            np.load(os.path.join(folder, "rule_hits.npy")), models, meta)


def main(repo, revision, set_path, local_dir, runs_repo, runs_revision, models_path,
         runs_dir, rebuild=False, onnx_files=None, precision=None):
    settings = Settings()
    set_directory = {"repo": repo, "revision": revision, "path": set_path}
    models_directory = {"repo": runs_repo, "revision": runs_revision, "path": models_path}
    onnx_directory, onnx_folder = None, None
    if onnx_files is not None:
        onnx_directory = {"repo": runs_repo, "revision": runs_revision,
                          "path": onnx_files, "precision": precision}
        onnx_folder, onnx_meta = read_dir(runs_repo, onnx_files, runs_dir, runs_revision)
        made_from = onnx_meta["models"]["path"]
        if made_from != models_path:
            raise ValueError(f"{onnx_files} is made from {made_from}, not {models_path}")
    inputs = {"set": set_path, "models": models_path, "onnx_files": onnx_files,
              "precision": precision}
    return reuse_or_make(runs_repo, "scores", inputs, runs_dir,
                         lambda folder: write_scores(folder, set_directory,
                                                     models_directory, onnx_directory,
                                                     onnx_folder, local_dir, runs_dir,
                                                     settings),
                         rebuild)


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "set_path", "local_dir", "runs_repo",
                     "runs_revision", "models_path", "runs_dir"),
                    rebuild=False, onnx_files=None, precision=None))
