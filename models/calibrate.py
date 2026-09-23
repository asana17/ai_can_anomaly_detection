"""Give every fitted model the score above which a row counts as an anomaly.

    python3 -m models.calibrate runs_repo revision models/<time> runs_dir local_dir [--rebuild] [--settings <file>] [--onnx-files <dir> --precision <precision>]

The thresholds come from the scores `scoring.score` gives the calibration set the
models' train set names, which no model was fitted on. A model reconstructs the rows
it was fitted on better than the rest, so a threshold taken from those would sit too
low. With `--onnx-files` each model is its ONNX file of `precision` in that directory,
made from the same fit.
"""

from __future__ import annotations

import json
import os
import platform

import numpy as np

from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import read_settings
from scoring import score


def quantile(scores, share: float):
    """Return the value that `share` of `scores` are above.

    With `share` 0.001, one score in a thousand comes out higher than that value.
    """
    return float(np.percentile(scores, 100 * (1 - share)))


def calibration_rows(scores, rule_hit):
    """Which rows a threshold is taken from, the rows scored that no rule hits."""
    # a row a rule already flags says nothing about where to put a model's threshold
    return ~np.isnan(scores).any(axis=1) & ~rule_hit


def thresholds_for(models, scores, *, target):
    """Return each of `models` with its threshold, from its column of `scores`.

    A model's threshold is the score that `target` of the rows are above.
    """
    return [{**model, "threshold": quantile(column, target)}
            for model, column in zip(models, scores.T)]


def write_thresholds(folder, runs_repo, revision, models_path, runs_dir, local_dir,
                     onnx_files, precision, settings):
    """Write `thresholds.json` into `folder`, and return what its `meta.json` adds.

    The calibration set is scored first, unless `runs_repo` holds its scores already.
    """
    _, fitted = read_dir(runs_repo, models_path, runs_dir, revision)
    at = fitted["calibration_set"]
    scores_directory = score.main(at["repo"], at["revision"], at["path"], local_dir,
                                  runs_repo, revision, models_path, runs_dir,
                                  onnx_files=onnx_files, precision=precision)
    scores, rule_hit, models, scored = score.fetch_scores(scores_directory, runs_dir)
    kept = calibration_rows(scores, rule_hit)
    thresholds = thresholds_for(models, scores[kept], target=settings.TARGET)
    with open(os.path.join(folder, "thresholds.json"), "w") as f:
        json.dump(thresholds, f, indent=2)
    return {"scores": scores_directory,
            **{name: scored[name] for name in ("models", "onnx_files", "calibration_set",
                                               "log_split", "grid", "min_speed")},
            "rows": int(kept.sum()),
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "platform": platform.platform()}}


def main(runs_repo, revision, models_path, runs_dir, local_dir, rebuild=False,
         dry_run=False, settings=None, onnx_files=None, precision=None):
    settings = read_settings(settings)
    inputs = {"models": models_path, "target": settings.TARGET, "onnx_files": onnx_files,
              "precision": precision}
    return reuse_or_make(runs_repo, "thresholds", inputs, runs_dir,
                         lambda folder: write_thresholds(folder, runs_repo, revision,
                                                         models_path, runs_dir,
                                                         local_dir, onnx_files,
                                                         precision, settings),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("runs_repo", "revision", "models_path", "runs_dir", "local_dir"),
                    rebuild=False, settings=None, onnx_files=None, precision=None))
