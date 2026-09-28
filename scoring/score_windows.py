"""Score every window of a calibration set or a test set with each window model.

    python3 -m scoring.score_windows repo revision <set> local_dir runs_repo revision window_models/<time> runs_dir [--rebuild] [--onnx-files window_onnx/<time>]

`<set>` is `calibration_sets/<time>` or `test_sets/<time>`. A window's score is saved
at its last row. `scores.npy` has the same rows, in the same order, as the scores
`scoring.score` saves for that set. With `--onnx-files` the models are the ones that
directory exported, each scoring with its float ONNX file.
"""

from __future__ import annotations

import json
import os
import platform

import numpy as np
import onnxruntime
import torch

from assemble.calibration_set import fetch_calibration_set
from assemble.test_set import fetch_test_set
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from models.fit import fetch_fitted_models
from models.fits import as_dict, models_from
from models.onnx_files import fetch_onnx_files, onnx_window_scorer
from models.torch_files import scale_of, torch_scorer
from preprocess.features.moving import moving
from preprocess.features.windows import positions, window_ends, window_rows

# windows a model scores at once. It bounds the memory, not the scores
WINDOWS = 100_000


def fetch_set_rows(directory, local_dir):
    """The rows of the calibration set or test set `directory` names, the segment id
    of each row, its `min_speed`, and the directories the rows came from."""
    at = (directory["repo"], directory["revision"], directory["path"], local_dir)
    if directory["path"].startswith("test_sets/"):
        got = fetch_test_set(*at)
        return got["raw"], got["seg"], got["min_speed"], got["dataset"]
    got = fetch_calibration_set(*at)
    return got["calibration"], got["seg"], got["min_speed"], got["dataset"]


def scores_of(models, scorer_of, rows, moving, segments, *, at_once):
    """One column per model of its score on each window of `moving` rows, at the
    window's last row, and how many windows each model scored.

    A window is `model.rows` rows next to each other in one segment, oldest first. A
    row where no window ends gets NaN. The windows are cut and scored `at_once` at a
    time.
    """
    position = positions(moving, segments)
    scores = np.full((len(rows), len(models)), np.nan, np.float32)
    windows = []
    for column, model in enumerate(models):
        ends = window_ends(position, rows=model.rows)
        score = scorer_of(model)
        for start in range(0, len(ends), at_once):
            part = ends[start:start + at_once]
            scores[part, column] = score(window_rows(rows, part, rows=model.rows))
        windows.append(len(ends))
        print(f"{model.name}, {len(ends)} windows scored", flush=True)
    return scores, windows


def write_scores(folder, set_directory, models_directory, onnx_directory, onnx_folder,
                 exported, local_dir, runs_dir):
    """Write each row's window scores into `folder`, and return what `meta.json` adds.

    Windows are cut from the moving rows, z-scored on the scale of the fit. The models
    score in torch. When `onnx_directory` names a window export, downloaded into
    `onnx_folder`, the models are the ones it `exported`, each scoring with its float
    ONNX file.
    """
    weights, fitted = fetch_fitted_models(models_directory["repo"],
                                          models_directory["revision"],
                                          models_directory["path"], runs_dir)
    raw, segments, min_speed, dataset = fetch_set_rows(set_directory, local_dir)
    if onnx_directory is None:
        models = models_from(fitted["inputs"]["models"])
        scorer_of = torch_scorer(weights)
        runtime = {"torch": torch.__version__}
    else:
        models = models_from(exported)
        scorer_of = onnx_window_scorer(onnx_folder)
        runtime = {"onnxruntime": onnxruntime.__version__}
    scores, windows = scores_of(models, scorer_of,
                                scale_of(weights).apply(raw),
                                moving(raw, min_speed=min_speed), segments,
                                at_once=WINDOWS)

    np.save(os.path.join(folder, "scores.npy"), scores)
    with open(os.path.join(folder, "models.json"), "w") as f:
        json.dump([as_dict(model) for model in models], f, indent=2)
    return {"models": models_directory, "onnx_files": onnx_directory, **dataset,
            "min_speed": min_speed, "rows": len(raw), "windows": windows,
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         **runtime, "platform": platform.platform()}}


def fetch_scores(directory, runs_dir):
    """The window scores in `directory`, the models of their columns, and its
    `meta.json`."""
    folder, meta = read_dir(directory["repo"], directory["path"], runs_dir,
                            directory["revision"])
    with open(os.path.join(folder, "models.json")) as f:
        models = json.load(f)
    return np.load(os.path.join(folder, "scores.npy")), models, meta


def main(repo, revision, set_path, local_dir, runs_repo, runs_revision, models_path,
         runs_dir, rebuild=False, dry_run=False, onnx_files=None):
    set_directory = {"repo": repo, "revision": revision, "path": set_path}
    models_directory = {"repo": runs_repo, "revision": runs_revision,
                        "path": models_path}
    onnx_directory, onnx_folder, exported = None, None, None
    if onnx_files is not None:
        # a window export holds float files alone
        onnx_directory = {"repo": runs_repo, "revision": runs_revision,
                          "path": onnx_files, "precision": "float"}
        onnx_folder, onnx_meta = fetch_onnx_files(runs_repo, runs_revision, onnx_files,
                                                  models_path, runs_dir)
        exported = onnx_meta["exported"]
    return reuse_or_make(runs_repo, "window_scores",
                         {"set": set_path, "models": models_path,
                          "onnx_files": onnx_files}, {}, runs_dir,
                         lambda folder: write_scores(folder, set_directory,
                                                     models_directory, onnx_directory,
                                                     onnx_folder, exported, local_dir,
                                                     runs_dir),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "set_path", "local_dir", "runs_repo",
                     "runs_revision", "models_path", "runs_dir"), rebuild=False,
                    onnx_files=None))
