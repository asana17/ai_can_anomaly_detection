import json
import os

import numpy as np
import torch

from models.fits import Var
from preprocess.features.signal_state import SIGNALS
from scoring import score_windows

REVISION = "ab" * 20
COMMIT = "de" * 20
SETS = ("calibration_set", "test_set", "log_split", "grid")
DATASET = {name: {"repo": "u/d", "revision": REVISION, "path": f"{name}s/20260101-000000"}
           for name in SETS}
ROWS = np.arange(4, dtype=np.float32)[:, None]
SEG = np.array([0, 0, 1, 1])


def sets_over(monkeypatch):
    """Fake a calibration set and a test set, both holding `ROWS`."""
    monkeypatch.setattr(score_windows, "fetch_calibration_set", lambda *args: {
        "calibration": ROWS, "seg": SEG, "min_speed": 5.0,
        "dataset": {name: DATASET[name]
                    for name in ("calibration_set", "log_split", "grid")}})
    monkeypatch.setattr(score_windows, "fetch_test_set", lambda *args: {
        "raw": ROWS, "seg": SEG, "min_speed": 5.0,
        "dataset": {name: DATASET[name] for name in ("test_set", "log_split", "grid")}})


def fetched(path, tmp_path):
    """What `fetch_set_rows` returns for the fake set at `path`."""
    return score_windows.fetch_set_rows(
        {"repo": "u/d", "revision": REVISION, "path": path}, str(tmp_path))


def test_a_calibration_set_gives_its_rows_and_their_segments(tmp_path, monkeypatch):
    sets_over(monkeypatch)
    rows, segments, min_speed, dataset = fetched("calibration_sets/20260101-000000",
                                                 tmp_path)

    assert np.array_equal(rows, ROWS) and np.array_equal(segments, SEG)
    assert min_speed == 5.0 and "calibration_set" in dataset


def test_a_test_set_gives_its_rows_and_their_segments(tmp_path, monkeypatch):
    sets_over(monkeypatch)
    rows, segments, min_speed, dataset = fetched("test_sets/20260101-000000", tmp_path)

    assert np.array_equal(rows, ROWS) and np.array_equal(segments, SEG)
    assert min_speed == 5.0 and "test_set" in dataset


class StandIn:
    """A stand-in window model of `rows` rows."""

    name = "stand-in"

    def __init__(self, rows):
        self.rows = rows


def test_a_window_scores_at_its_last_row_and_other_rows_get_nan():
    rows = np.arange(10, dtype=np.float32)[:, None]
    # row 4 is not moving, and row 8 starts a new segment
    moving = np.array([True] * 4 + [False] + [True] * 5)
    segments = np.array([0] * 8 + [1] * 2)
    got = {}

    def scorer_of(model):
        """Score a window by its last row's value, keeping the windows it was given."""
        def score(windows):
            got[model.rows] = windows
            return windows[:, -1, 0]
        return score

    scores, windows = score_windows.scores_of([StandIn(3), StandIn(2)], scorer_of,
                                              rows, moving, segments)

    assert got[3][:, :, 0].tolist() == [[0, 1, 2], [1, 2, 3], [5, 6, 7]], "oldest first"
    assert np.flatnonzero(~np.isnan(scores[:, 0])).tolist() == [2, 3, 7]
    assert scores[[2, 3, 7], 0].tolist() == [2, 3, 7]
    assert np.flatnonzero(~np.isnan(scores[:, 1])).tolist() == [1, 2, 3, 6, 7, 9]
    assert windows == [3, 6]


def moving_rows(count):
    """`count` rows of random signals, all moving."""
    rows = np.random.default_rng(0).normal(size=(count, len(SIGNALS)))
    rows[:, SIGNALS.index("wheel_speed")] = 10.0
    return rows.astype(np.float32)


def fitted_var(monkeypatch, model):
    """A window fit holding `model`, a var fitted on random windows. Returns how the
    var scores windows."""
    windows = np.random.default_rng(1).normal(size=(64, model.rows, len(SIGNALS)))
    tensors, score, _ = model.fit(windows.astype(np.float32))
    weights = {"scale.mean": torch.zeros(len(SIGNALS)),
               "scale.std": torch.ones(len(SIGNALS)), **tensors}
    monkeypatch.setattr(score_windows, "fetch_fitted_models", lambda *args: (
        weights, {"inputs": {"models": [{"model": "var", "rows": model.rows}]}}))
    return score


def test_a_run_keeps_the_window_scores_and_rule_hits_of_every_row_of_the_set(
        tmp_path, hub, monkeypatch):
    score = fitted_var(monkeypatch, Var(3))
    rows = moving_rows(6)
    rows[3, SIGNALS.index("wheel_speed")] = 1.0      # row 3 is not moving
    monkeypatch.setattr(score_windows, "fetch_test_set", lambda *args: {
        "raw": rows, "seg": np.zeros(6), "min_speed": 5.0,
        "dataset": {name: DATASET[name] for name in ("test_set", "log_split", "grid")}})
    monkeypatch.setattr(score_windows, "rule_hits", lambda raw, min_speed: np.array(
        [False, True, False, True, False, False]))
    hub.files = {}
    made = score_windows.main("u/d", REVISION, "test_sets/20260101-000000",
                              str(tmp_path), "u/runs", COMMIT,
                              "window_models/20260101-000000", str(tmp_path))

    folder = tmp_path / made["path"]
    assert made["path"].startswith("window_scores/")
    assert sorted(os.listdir(folder)) == ["meta.json", "models.json", "rule_hits.npy",
                                          "scores.npy"]
    scores = np.load(folder / "scores.npy")
    assert scores.shape == (6, 1), "a row of the set each, a column of a model each"
    assert np.flatnonzero(~np.isnan(scores[:, 0])).tolist() == [2]
    assert np.allclose(scores[2, 0], score(rows[None, :3]))
    hits = np.load(folder / "rule_hits.npy")
    assert hits.tolist() == [False, True, False, False, False, False], \
        "a rule hit on a standing row is no hit"
    assert json.load(open(folder / "models.json")) == [{"model": "var", "rows": 3}]
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"set": "test_sets/20260101-000000",
                              "models": "window_models/20260101-000000"}
    assert meta["rows"] == 6 and meta["windows"] == [1]
    assert meta["test_set"] == DATASET["test_set"]
