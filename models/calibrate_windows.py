"""Give every fitted window model the score above which a window counts as an anomaly.

    python3 -m models.calibrate_windows runs_repo revision window_models/<time> runs_dir local_dir [--rebuild] [--onnx-files window_onnx/<time>]

The thresholds come from the scores `scoring.score_windows` gives the windows of the
calibration set the models' train set names. No model was fitted on them. Each model
takes its threshold from its own windows alone. With `--onnx-files` the models are the
ones that window export holds, each its float ONNX file, made from the same fit.
"""

from __future__ import annotations

import json
import os
import platform

import numpy as np

from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import CalibrateSettings
from models.calibrate import quantile
from scoring import score_windows


def thresholds_for(models, scores, *, target):
    """Return each of `models` with its threshold, from its column of `scores`.

    A model's threshold is the score that `target` of its windows are above. A row
    where no window of the model ends has NaN, and is left out.
    """
    return [{**model, "threshold": quantile(column[~np.isnan(column)], target)}
            for model, column in zip(models, scores.T)]


def write_thresholds(folder, runs_repo, revision, models_path, runs_dir, local_dir,
                     onnx_files, settings, rebuild):
    """Write `thresholds.json` into `folder`, and return what its `meta.json` adds.

    The calibration set is scored first, unless `runs_repo` holds its scores already
    and `rebuild` is false.
    """
    _, fitted = read_dir(runs_repo, models_path, runs_dir, revision)
    at = fitted["calibration_set"]
    scores_directory = score_windows.main(at["repo"], at["revision"], at["path"],
                                          local_dir, runs_repo, revision, models_path,
                                          runs_dir, rebuild=rebuild,
                                          onnx_files=onnx_files)
    scores, models, scored = score_windows.fetch_scores(scores_directory, runs_dir)
    thresholds = thresholds_for(models, scores, target=settings.TARGET)
    with open(os.path.join(folder, "thresholds.json"), "w") as f:
        json.dump(thresholds, f, indent=2)
    return {"scores": scores_directory,
            **{name: scored[name] for name in ("models", "onnx_files", "calibration_set",
                                               "log_split", "grid", "min_speed")},
            "windows": [int(count) for count in (~np.isnan(scores)).sum(axis=0)],
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "platform": platform.platform()}}


def main(runs_repo, revision, models_path, runs_dir, local_dir, rebuild=False,
         dry_run=False, settings=CalibrateSettings(), onnx_files=None):
    return reuse_or_make(runs_repo, "window_thresholds",
                         {"models": models_path, "onnx_files": onnx_files},
                         {"target": settings.TARGET}, runs_dir,
                         lambda folder: write_thresholds(folder, runs_repo, revision,
                                                         models_path, runs_dir,
                                                         local_dir, onnx_files,
                                                         settings, rebuild),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("runs_repo", "revision", "models_path", "runs_dir", "local_dir"),
                    rebuild=False, onnx_files=None))
