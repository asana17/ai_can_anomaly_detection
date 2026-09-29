import json
import os

import numpy as np

from common.settings import CalibrateSettings
from models import calibrate
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20
COMMIT = "de" * 20

WHERE = {"repo": "u/d", "revision": REVISION}


def test_the_threshold_is_the_lowest_at_the_target_alarms_an_hour():
    # windows of one flag at rows 10, 30, 50, 70 and 90, scores 9 to 5
    column = np.zeros(100, np.float32)
    column[[10, 30, 50, 70, 90]] = [9.0, 8.0, 7.0, 6.0, 5.0]
    segments = np.zeros(100, int)
    none = np.zeros(100, bool)
    assert calibrate.threshold_for(column, none, segments, 1.0, n=10, k=1,
                                   target=2) == 7.0
    assert calibrate.threshold_for(column, none, segments, 1.0, n=10, k=1,
                                   target=5) == 0.0


def test_the_rules_count_against_the_target():
    column = np.zeros(100, np.float32)
    column[[10, 30, 50]] = [9.0, 8.0, 7.0]
    rule_hit = np.zeros(100, bool)
    rule_hit[70] = True                     # one alarm the rules raise on their own
    assert calibrate.threshold_for(column, rule_hit, np.zeros(100, int), 1.0, n=10,
                                   k=1, target=2) == 8.0


def test_the_alarm_is_held_to_its_target_at_k():
    column = np.zeros(100, np.float32)
    column[10:13] = 9.0                     # three rows in a row
    column[50] = 8.0                        # one row alone
    segments = np.zeros(100, int)
    none = np.zeros(100, bool)
    # at k = 3 the lone row raises no alarm, so the threshold may go below it
    assert calibrate.threshold_for(column, none, segments, 1.0, n=10, k=3,
                                   target=1) == 0.0


SCORES = {"set": "calibration_sets/20260101-000000", "models": "models/20260101-000000",
          "onnx_files": None, "precision": None}


def run_and_scores(hub, monkeypatch, scores):
    """A fit on the calibration set `calibration_sets/20260101-000000`, and the scores
    of that set it already has. The set's rows are all moving, in one segment."""
    rows = np.zeros((len(scores), len(SIGNALS)), np.float32)
    rows[:, SIGNALS.index("wheel_speed")] = 50.0
    monkeypatch.setattr(calibrate.score_windows, "fetch_set_rows",
                        lambda *args: (rows, np.zeros(len(scores), int), 5.0, {}))
    models = {"repo": "u/runs", "revision": REVISION, "path": "models/20260101-000000"}
    calibration_set = dict(WHERE, path="calibration_sets/20260101-000000")
    hub.files = {
        "models/20260101-000000/meta.json": {"calibration_set": calibration_set},
        "scores/20260101-000000/meta.json": {
            "inputs": SCORES, "models": models, "onnx_files": None,
            "calibration_set": calibration_set,
            "log_split": dict(WHERE, path="log_splits/20260101-000000"),
            "grid": dict(WHERE, path="grids/20260101-000000"), "min_speed": 5.0,
            "scored": int((~np.isnan(scores[:, 0])).sum())},
        "scores/20260101-000000/models.json": [{"model": "pca", "k": 2}],
        "scores/20260101-000000/scores.npy": scores,
        "scores/20260101-000000/rule_hits.npy": np.zeros(len(scores), bool)}


def test_a_threshold_is_kept_for_every_model_scored(tmp_path, hub, monkeypatch):
    scores = np.arange(21, dtype=np.float32)[:, None]
    scores[0] = np.nan
    run_and_scores(hub, monkeypatch, scores)
    made = calibrate.main("u/runs", COMMIT, "models/20260101-000000", str(tmp_path),
                          str(tmp_path))

    folder = tmp_path / made["path"]
    assert sorted(os.listdir(folder)) == ["meta.json", "thresholds.json"]
    kept = json.load(open(folder / "thresholds.json"))
    assert [k["model"] for k in kept] == ["pca"] and kept[0]["threshold"] > 0
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"models": "models/20260101-000000",
                              "row_target": CalibrateSettings().ROW_TARGET,
                              "row_k": CalibrateSettings().ROW_K, "n": 10,
                              "onnx_files": None, "precision": None}
    assert meta["scores"]["path"] == "scores/20260101-000000", "the scores are reused"
    assert meta["rows"] == 20


def test_the_calibration_set_is_scored_as_the_thresholds_are_asked_for(tmp_path, hub,
                                                                     monkeypatch):
    run_and_scores(hub, monkeypatch, np.ones((3, 1), np.float32))
    asked = []
    monkeypatch.setattr(calibrate.score, "main", lambda *args, **options: (
        asked.append((args[2], options)) or
        {"repo": "u/runs", "revision": REVISION, "path": "scores/20260101-000000"}))
    calibrate.main("u/runs", COMMIT, "models/20260101-000000", str(tmp_path),
                   str(tmp_path), onnx_files="quantize/20260101-000000", precision="int8")

    assert asked == [("calibration_sets/20260101-000000",
                      {"rebuild": False, "onnx_files": "quantize/20260101-000000",
                       "precision": "int8"})]


def test_a_rebuild_scores_the_calibration_set_again(tmp_path, hub, monkeypatch):
    run_and_scores(hub, monkeypatch, np.ones((3, 1), np.float32))
    asked = []
    monkeypatch.setattr(calibrate.score, "main", lambda *args, **options: (
        asked.append(options["rebuild"]) or
        {"repo": "u/runs", "revision": REVISION, "path": "scores/20260101-000000"}))
    calibrate.main("u/runs", COMMIT, "models/20260101-000000", str(tmp_path),
                   str(tmp_path), rebuild=True)

    assert asked == [True]
