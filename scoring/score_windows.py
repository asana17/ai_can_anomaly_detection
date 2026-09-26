"""Score every window of a calibration set or a test set with each window model.

    python3 -m scoring.score_windows repo revision <set> local_dir runs_repo revision window_models/<time> runs_dir [--rebuild]

`<set>` is `calibration_sets/<time>` or `test_sets/<time>`. A window's score is saved
at its last row. `scores.npy` has the same rows, in the same order, as the scores
`scoring.score` saves for that set.
"""

from __future__ import annotations

import numpy as np

from assemble.calibration_set import fetch_calibration_set
from assemble.test_set import fetch_test_set
from preprocess.features.windows import positions, window_ends, window_rows


def fetch_set_rows(directory, local_dir):
    """The rows of the calibration set or test set `directory` names, the segment id
    of each row, its `min_speed`, and the directories the rows came from."""
    at = (directory["repo"], directory["revision"], directory["path"], local_dir)
    if directory["path"].startswith("test_sets/"):
        got = fetch_test_set(*at)
        return got["raw"], got["seg"], got["min_speed"], got["dataset"]
    got = fetch_calibration_set(*at)
    return got["calibration"], got["seg"], got["min_speed"], got["dataset"]


def scores_of(models, scorer_of, rows, moving, segments):
    """One column per model of its score on each window of `moving` rows, at the
    window's last row, and how many windows each model scored.

    A window is `model.rows` rows next to each other in one segment, oldest first. A
    row where no window ends gets NaN.
    """
    position = positions(moving, segments)
    scores = np.full((len(rows), len(models)), np.nan, np.float32)
    windows = []
    for column, model in enumerate(models):
        ends = window_ends(position, rows=model.rows)
        windows_of_model = window_rows(rows, ends, rows=model.rows)
        scores[ends, column] = scorer_of(model)(windows_of_model)
        windows.append(len(ends))
        print(f"{model.name}, {len(ends)} windows scored", flush=True)
    return scores, windows
