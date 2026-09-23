import json
import os

import numpy as np
import pytest

from common.settings import CalibrateSettings
from models import calibrate

REVISION = "ab" * 20
COMMIT = "de" * 20

WHERE = {"repo": "u/d", "revision": REVISION}


def test_the_quantile_leaves_that_share_of_the_scores_above_it():
    scores = np.arange(1000, dtype=float)
    assert (scores > calibrate.quantile(scores, 0.1)).mean() == pytest.approx(0.1, 0.01)


def test_a_row_with_no_score_or_hit_by_a_rule_sets_no_threshold():
    scores = np.array([[np.nan], [1.0], [2.0]], np.float32)
    rule_hit = np.array([False, False, True])

    assert calibrate.calibration_rows(scores, rule_hit).tolist() == [False, True, False]


SCORES = {"set": "calibration_sets/20260101-000000", "models": "models/20260101-000000",
          "onnx_files": None, "precision": None}


def run_and_scores(hub, scores):
    """A fit on the calibration set `calibration_sets/20260101-000000`, and the scores
    of that set it already has."""
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


def test_a_threshold_is_kept_for_every_model_scored(tmp_path, hub):
    scores = np.arange(21, dtype=np.float32)[:, None]
    scores[0] = np.nan
    run_and_scores(hub, scores)
    made = calibrate.main("u/runs", COMMIT, "models/20260101-000000", str(tmp_path),
                          str(tmp_path))

    folder = tmp_path / made["path"]
    assert sorted(os.listdir(folder)) == ["meta.json", "thresholds.json"]
    kept = json.load(open(folder / "thresholds.json"))
    assert [k["model"] for k in kept] == ["pca"] and kept[0]["threshold"] > 0
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"models": "models/20260101-000000",
                              "target": CalibrateSettings().TARGET, "onnx_files": None,
                              "precision": None}
    assert meta["scores"]["path"] == "scores/20260101-000000", "the scores are reused"
    assert meta["rows"] == 20


def test_the_calibration_set_is_scored_as_the_thresholds_are_asked_for(tmp_path, hub,
                                                                     monkeypatch):
    run_and_scores(hub, np.ones((3, 1), np.float32))
    asked = []
    monkeypatch.setattr(calibrate.score, "main", lambda *args, **options: (
        asked.append((args[2], options)) or
        {"repo": "u/runs", "revision": REVISION, "path": "scores/20260101-000000"}))
    calibrate.main("u/runs", COMMIT, "models/20260101-000000", str(tmp_path),
                   str(tmp_path), onnx_files="quantize/20260101-000000", precision="int8")

    assert asked == [("calibration_sets/20260101-000000",
                      {"onnx_files": "quantize/20260101-000000", "precision": "int8"})]
