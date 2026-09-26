import json
import os

import numpy as np
import pytest

from common.settings import CalibrateSettings
from models import calibrate_windows

REVISION = "ab" * 20
COMMIT = "de" * 20
WHERE = {"repo": "u/d", "revision": REVISION}
MODELS = [{"model": "var", "rows": 3}, {"model": "var", "rows": 5}]


def test_a_threshold_is_taken_from_the_model_s_own_windows():
    scores = np.full((1000, 2), np.nan, np.float32)
    # the first model has windows on rows 0 to 499, the second on rows 500 to 999
    scores[:500, 0] = np.arange(500)
    scores[500:, 1] = np.arange(500) + 1000.0
    kept = calibrate_windows.thresholds_for(MODELS, scores, target=0.1)

    assert [k["rows"] for k in kept] == [3, 5]
    assert (scores[:500, 0] > kept[0]["threshold"]).mean() == pytest.approx(0.1, 0.01)
    assert (scores[500:, 1] > kept[1]["threshold"]).mean() == pytest.approx(0.1, 0.01)


def fit_and_scores(hub, scores):
    """A window fit on the calibration set `calibration_sets/20260101-000000`, and the
    window scores of that set it already has."""
    models = {"repo": "u/runs", "revision": REVISION,
              "path": "window_models/20260101-000000"}
    calibration_set = dict(WHERE, path="calibration_sets/20260101-000000")
    hub.files = {
        "window_models/20260101-000000/meta.json": {"calibration_set": calibration_set},
        "window_scores/20260101-000000/meta.json": {
            "inputs": {"set": "calibration_sets/20260101-000000",
                       "models": "window_models/20260101-000000"},
            "models": models, "calibration_set": calibration_set,
            "log_split": dict(WHERE, path="log_splits/20260101-000000"),
            "grid": dict(WHERE, path="grids/20260101-000000"), "min_speed": 5.0,
            "windows": [0, 0]},
        "window_scores/20260101-000000/models.json": MODELS,
        "window_scores/20260101-000000/scores.npy": scores}


def test_a_threshold_is_kept_for_every_window_model(tmp_path, hub):
    scores = np.full((21, 2), np.nan, np.float32)
    scores[2:, 0] = np.arange(19)
    scores[4:, 1] = np.arange(17)
    fit_and_scores(hub, scores)
    made = calibrate_windows.main("u/runs", COMMIT, "window_models/20260101-000000",
                                  str(tmp_path), str(tmp_path))

    folder = tmp_path / made["path"]
    assert made["path"].startswith("window_thresholds/")
    assert sorted(os.listdir(folder)) == ["meta.json", "thresholds.json"]
    kept = json.load(open(folder / "thresholds.json"))
    assert [k["rows"] for k in kept] == [3, 5]
    assert all(k["threshold"] > 0 for k in kept)
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"models": "window_models/20260101-000000",
                              "target": CalibrateSettings().TARGET}
    assert meta["scores"]["path"] == "window_scores/20260101-000000", "reused"
    assert meta["windows"] == [19, 17], "counted from the scores the thresholds used"
