"""Give every fitted model the score above which a row counts as an anomaly.

    python3 -m models.calibrate runs_repo revision models/<time> runs_dir local_dir [--rebuild] [--onnx-files <dir> --precision <precision>]

The thresholds come from the scores `scoring.score` gives the calibration set the
models' train set names, which no model was fitted on. A model reconstructs the rows
it was fitted on better than the rest, so a threshold taken from those would sit too
low. Each model's threshold is the lowest at which the alarm on every tick, its flags
or a rule's in `ROW_K` of the last N rows, rises no more than `ROW_TARGET` times an
hour. With `--onnx-files` each model is its ONNX file of `precision` in that directory,
made from the same fit.
"""

from __future__ import annotations

import json
import os
import platform

import numpy as np

from common.cli import arguments
from common.hub_dirs import read_dir, reuse_or_make
from common.settings import CalibrateSettings, GridSettings, TestRunSettings
from detect.alarm import alarmed_rows
from preprocess.features.moving import moving
from scoring import score, score_windows


def alarms(alarmed):
    """How many times an alarm rises, `alarmed` holding one flag per row."""
    return int((alarmed & ~np.r_[False, alarmed[:-1]]).sum())


def threshold_for(column, rule_hit, segments, hours, *, n, k, target):
    """The lowest of `column`'s scores at which the alarm on every tick rises no more
    than `target` times an hour. A row with no score has NaN, and never flags.

    When the rules alone raise more, it is the highest score, which nothing is above.
    """
    candidates = np.unique(column[~np.isnan(column)])[::-1]
    # the alarm rises more often the further down the candidates the threshold goes
    low, high = 0, len(candidates) - 1
    while low < high:
        middle = (low + high + 1) // 2
        rising = alarms(alarmed_rows(column, candidates[middle], rule_hit, segments, n,
                                     k))
        if rising <= target * hours:
            low = middle
        else:
            high = middle - 1
    return float(candidates[low])


def thresholds_for(models, scores, rule_hit, segments, hours, *, n, k, target):
    """Return each of `models` with its threshold, from its column of `scores`."""
    return [{**model, "threshold": threshold_for(column, rule_hit, segments, hours,
                                                 n=n, k=k, target=target)}
            for model, column in zip(models, scores.T)]


def write_thresholds(folder, runs_repo, revision, models_path, runs_dir, local_dir,
                     onnx_files, precision, settings, rebuild):
    """Write `thresholds.json` into `folder`, and return what its `meta.json` adds.

    The calibration set is scored first, unless `runs_repo` holds its scores already
    and `rebuild` is false.
    """
    _, fitted = read_dir(runs_repo, models_path, runs_dir, revision)
    at = fitted["calibration_set"]
    scores_directory = score.main(at["repo"], at["revision"], at["path"], local_dir,
                                  runs_repo, revision, models_path, runs_dir,
                                  rebuild=rebuild, onnx_files=onnx_files,
                                  precision=precision)
    scores, rule_hit, models, scored = score.fetch_scores(scores_directory, runs_dir)
    rows, segments, min_speed, _ = score_windows.fetch_set_rows(at, local_dir)
    hours = moving(rows, min_speed=min_speed).sum() * GridSettings.PERIOD / 3600
    thresholds = thresholds_for(models, scores, rule_hit, segments, hours,
                                n=TestRunSettings.N, k=settings.ROW_K,
                                target=settings.ROW_TARGET)
    with open(os.path.join(folder, "thresholds.json"), "w") as f:
        json.dump(thresholds, f, indent=2)
    return {"scores": scores_directory,
            **{name: scored[name] for name in ("models", "onnx_files", "calibration_set",
                                               "log_split", "grid", "min_speed")},
            "rows": int((~np.isnan(scores).any(axis=1)).sum()),
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "platform": platform.platform()}}


def main(runs_repo, revision, models_path, runs_dir, local_dir, rebuild=False,
         dry_run=False, settings=CalibrateSettings(), onnx_files=None, precision=None):
    return reuse_or_make(runs_repo, "thresholds",
                         {"models": models_path, "onnx_files": onnx_files},
                         {"row_target": settings.ROW_TARGET, "row_k": settings.ROW_K,
                          "n": TestRunSettings.N, "precision": precision}, runs_dir,
                         lambda folder: write_thresholds(folder, runs_repo, revision,
                                                         models_path, runs_dir,
                                                         local_dir, onnx_files,
                                                         precision, settings,
                                                         rebuild),
                         rebuild, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("runs_repo", "revision", "models_path", "runs_dir", "local_dir"),
                    rebuild=False, onnx_files=None, precision=None))
