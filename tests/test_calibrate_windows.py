import json
import os

import numpy as np
import pytest

from common.settings import CalibrateSettings
from models import calibrate_windows
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20
COMMIT = "de" * 20
WHERE = {"repo": "u/d", "revision": REVISION}
MODELS = [{"model": "var", "rows": 3}, {"model": "var", "rows": 5}]


def test_a_threshold_is_taken_from_the_model_s_own_windows():
    scores = np.full((1000, 2), np.nan, np.float32)
    # the first model has windows on every other row of 0 to 499, the second of 500 on
    scores[:500:2, 0] = np.arange(250)
    scores[500::2, 1] = np.arange(250) + 1000.0
    kept = calibrate_windows.thresholds_for(MODELS, scores, np.zeros(1000, int), 1.0,
                                            n=1, target=5)

    assert [k["rows"] for k in kept] == [3, 5]
    # with n = 1 each flagged window raises its own alarm, so 5 an hour flags 5
    assert kept[0]["threshold"] == 244.0
    assert kept[1]["threshold"] == 1244.0


def test_flags_within_n_rows_raise_one_alarm():
    column = np.zeros(100, np.float32)
    column[[10, 15, 19, 50]] = 9.0            # 10 to 19 is one alarm, 50 another
    column[[70]] = 5.0
    segments = np.zeros(100, int)
    assert calibrate_windows.threshold_for(column, segments, 1.0, n=10, target=2) == 5.0
    assert calibrate_windows.threshold_for(column, segments, 1.0, n=10, target=1) == 9.0


def test_a_new_segment_raises_a_new_alarm():
    column = np.zeros(20, np.float32)
    column[[4, 6]] = 9.0
    assert calibrate_windows.alarms(column > 1, np.zeros(20, int), 10) == 1
    assert calibrate_windows.alarms(column > 1, np.r_[[0] * 5, [1] * 15], 10) == 2


def fit_and_scores(hub, monkeypatch, scores, onnx_files=None):
    """A window fit on the calibration set `calibration_sets/20260101-000000`, and the
    window scores of that set it already has, scored as `onnx_files`, in torch when
    None. The set's rows are all moving, in one segment."""
    rows = np.zeros((len(scores), len(SIGNALS)), np.float32)
    rows[:, SIGNALS.index("wheel_speed")] = 50.0
    monkeypatch.setattr(calibrate_windows.score_windows, "fetch_set_rows",
                        lambda *args: (rows, np.zeros(len(scores), int), 5.0, {}))
    models = {"repo": "u/runs", "revision": REVISION,
              "path": "window_models/20260101-000000"}
    calibration_set = dict(WHERE, path="calibration_sets/20260101-000000")
    hub.files = {
        "window_models/20260101-000000/meta.json": {"calibration_set": calibration_set},
        "window_scores/20260101-000000/meta.json": {
            "inputs": {"set": "calibration_sets/20260101-000000",
                       "models": "window_models/20260101-000000",
                       "onnx_files": onnx_files},
            "models": models,
            "onnx_files": onnx_files and {"repo": "u/runs", "revision": REVISION,
                                          "path": onnx_files, "precision": "float"},
            "calibration_set": calibration_set,
            "log_split": dict(WHERE, path="log_splits/20260101-000000"),
            "grid": dict(WHERE, path="grids/20260101-000000"), "min_speed": 5.0,
            "windows": [0, 0]},
        "window_scores/20260101-000000/models.json": MODELS,
        "window_scores/20260101-000000/scores.npy": scores}


def test_a_threshold_is_kept_for_every_window_model(tmp_path, hub, monkeypatch):
    scores = np.full((21, 2), np.nan, np.float32)
    scores[2:, 0] = np.arange(19)
    scores[4:, 1] = np.arange(17)
    fit_and_scores(hub, monkeypatch, scores)
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
                              "window_target": CalibrateSettings().WINDOW_TARGET,
                              "n": 10, "onnx_files": None}
    assert meta["scores"]["path"] == "window_scores/20260101-000000", "reused"
    assert meta["windows"] == [19, 17], "counted from the scores the thresholds used"


def test_the_thresholds_of_a_window_export_come_from_its_scores(tmp_path, hub,
                                                               monkeypatch):
    scores = np.full((21, 2), np.nan, np.float32)
    scores[2:, 0] = np.arange(19)
    scores[4:, 1] = np.arange(17)
    fit_and_scores(hub, monkeypatch, scores, onnx_files="window_onnx/20260101-000000")
    hub.files["window_onnx/20260101-000000/meta.json"] = {
        "models": {"path": "window_models/20260101-000000"}, "exported": MODELS}
    made = calibrate_windows.main("u/runs", COMMIT, "window_models/20260101-000000",
                                  str(tmp_path), str(tmp_path),
                                  onnx_files="window_onnx/20260101-000000")

    meta = json.load(open(tmp_path / made["path"] / "meta.json"))
    assert meta["inputs"]["onnx_files"] == "window_onnx/20260101-000000"
    assert meta["scores"]["path"] == "window_scores/20260101-000000", "reused"
    assert meta["onnx_files"]["path"] == "window_onnx/20260101-000000"


def test_a_rebuild_scores_the_calibration_set_again(tmp_path, hub, monkeypatch):
    scores = np.full((21, 2), np.nan, np.float32)
    scores[2:, 0] = np.arange(19)
    scores[4:, 1] = np.arange(17)
    fit_and_scores(hub, monkeypatch, scores)
    given = []
    real = calibrate_windows.score_windows.main
    monkeypatch.setattr(calibrate_windows.score_windows, "main",
                        lambda *args, rebuild, **kwargs: (
                            given.append(rebuild) or real(*args, **kwargs)))
    calibrate_windows.main("u/runs", COMMIT, "window_models/20260101-000000",
                           str(tmp_path), str(tmp_path), rebuild=True)

    assert given == [True]
