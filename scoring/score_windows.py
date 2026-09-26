"""Score every window of a calibration set or a test set with each window model.

    python3 -m scoring.score_windows repo revision <set> local_dir runs_repo revision window_models/<time> runs_dir [--rebuild]

`<set>` is `calibration_sets/<time>` or `test_sets/<time>`. A window's score is saved
at its last row. `scores.npy` has the same rows, in the same order, as the scores
`scoring.score` saves for that set.
"""

from __future__ import annotations

import json
import os
import platform

import numpy as np
import torch

from assemble.calibration_set import fetch_calibration_set
from assemble.test_set import fetch_test_set
from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from models.fit import fetch_fitted_models
from models.fits import as_dict, models_from
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


def write_scores(folder, set_directory, models_directory, local_dir, runs_dir):
    """Write each row's window scores into `folder`, and return what `meta.json` adds.

    Windows are cut from the moving rows, z-scored on the scale of the fit. The models
    score in torch.
    """
    weights, fitted = fetch_fitted_models(models_directory["repo"],
                                          models_directory["revision"],
                                          models_directory["path"], runs_dir)
    raw, segments, min_speed, dataset = fetch_set_rows(set_directory, local_dir)
    models = models_from(fitted["inputs"]["models"])
    scores, windows = scores_of(models, torch_scorer(weights),
                                scale_of(weights).apply(raw),
                                moving(raw, min_speed=min_speed), segments,
                                at_once=WINDOWS)

    np.save(os.path.join(folder, "scores.npy"), scores)
    with open(os.path.join(folder, "models.json"), "w") as f:
        json.dump([as_dict(model) for model in models], f, indent=2)
    return {"models": models_directory, **dataset, "min_speed": min_speed,
            "rows": len(raw), "windows": windows,
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "torch": torch.__version__, "platform": platform.platform()}}


def fetch_scores(directory, runs_dir):
    """The window scores in `directory`, the models of their columns, and its
    `meta.json`."""
    folder, meta = read_dir(directory["repo"], directory["path"], runs_dir,
                            directory["revision"])
    with open(os.path.join(folder, "models.json")) as f:
        models = json.load(f)
    return np.load(os.path.join(folder, "scores.npy")), models, meta


def main(repo, revision, set_path, local_dir, runs_repo, runs_revision, models_path,
         runs_dir, rebuild=False, dry_run=False):
    set_directory = {"repo": repo, "revision": revision, "path": set_path}
    models_directory = {"repo": runs_repo, "revision": runs_revision,
                        "path": models_path}
    return reuse_or_make(runs_repo, "window_scores",
                         {"set": set_path, "models": models_path}, {}, runs_dir,
                         lambda folder: write_scores(folder, set_directory,
                                                     models_directory, local_dir,
                                                     runs_dir),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("repo", "revision", "set_path", "local_dir", "runs_repo",
                     "runs_revision", "models_path", "runs_dir"), rebuild=False))
