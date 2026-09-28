import json
import os

import numpy as np
import pytest
import torch

from deploy.export import write_onnx_files
from models.fits import FitArguments, Var, WindowNonlinearAe, as_dict
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
                                              rows, moving, segments, at_once=100)

    assert got[3][:, :, 0].tolist() == [[0, 1, 2], [1, 2, 3], [5, 6, 7]], "oldest first"
    assert np.flatnonzero(~np.isnan(scores[:, 0])).tolist() == [2, 3, 7]
    assert scores[[2, 3, 7], 0].tolist() == [2, 3, 7]
    assert np.flatnonzero(~np.isnan(scores[:, 1])).tolist() == [1, 2, 3, 6, 7, 9]
    assert windows == [3, 6]


def test_windows_scored_a_few_at_a_time_score_as_all_at_once():
    rows = np.random.default_rng(0).normal(size=(20, 2)).astype(np.float32)
    moving = np.ones(20, dtype=bool)
    segments = np.array([0] * 12 + [1] * 8)

    def scorer_of(model):
        return lambda windows: windows.sum(axis=(1, 2))

    at_once, _ = score_windows.scores_of([StandIn(3)], scorer_of, rows, moving,
                                         segments, at_once=100)
    in_parts, _ = score_windows.scores_of([StandIn(3)], scorer_of, rows, moving,
                                          segments, at_once=4)
    assert np.array_equal(in_parts, at_once, equal_nan=True)


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


def test_a_run_keeps_the_window_scores_of_every_row_of_the_set(tmp_path, hub,
                                                               monkeypatch):
    score = fitted_var(monkeypatch, Var(3))
    rows = moving_rows(6)
    rows[3, SIGNALS.index("wheel_speed")] = 1.0      # row 3 is not moving
    monkeypatch.setattr(score_windows, "fetch_test_set", lambda *args: {
        "raw": rows, "seg": np.zeros(6), "min_speed": 5.0,
        "dataset": {name: DATASET[name] for name in ("test_set", "log_split", "grid")}})
    hub.files = {}
    made = score_windows.main("u/d", REVISION, "test_sets/20260101-000000",
                              str(tmp_path), "u/runs", COMMIT,
                              "window_models/20260101-000000", str(tmp_path))

    folder = tmp_path / made["path"]
    assert made["path"].startswith("window_scores/")
    assert sorted(os.listdir(folder)) == ["meta.json", "models.json", "scores.npy"]
    scores = np.load(folder / "scores.npy")
    assert scores.shape == (6, 1), "a row of the set each, a column of a model each"
    assert np.flatnonzero(~np.isnan(scores[:, 0])).tolist() == [2]
    assert np.allclose(scores[2, 0], score(rows[None, :3]))
    assert json.load(open(folder / "models.json")) == [{"model": "var", "rows": 3}]
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"set": "test_sets/20260101-000000",
                              "models": "window_models/20260101-000000",
                              "onnx_files": None}
    assert meta["rows"] == 6 and meta["windows"] == [1]
    assert meta["test_set"] == DATASET["test_set"]


def test_the_scores_read_back_as_they_were_written(tmp_path, hub, monkeypatch):
    fitted_var(monkeypatch, Var(3))
    rows = moving_rows(6)
    monkeypatch.setattr(score_windows, "fetch_test_set", lambda *args: {
        "raw": rows, "seg": np.zeros(6), "min_speed": 5.0,
        "dataset": {name: DATASET[name] for name in ("test_set", "log_split", "grid")}})
    hub.files = {}
    made = score_windows.main("u/d", REVISION, "test_sets/20260101-000000",
                              str(tmp_path), "u/runs", COMMIT,
                              "window_models/20260101-000000", str(tmp_path))
    written = np.load(tmp_path / made["path"] / "scores.npy")

    scores, models, meta = score_windows.fetch_scores(made, str(tmp_path))
    assert np.array_equal(scores, written, equal_nan=True)
    assert models == [{"model": "var", "rows": 3}]
    assert meta["windows"] == [4]


def exported_window_ae(monkeypatch, tmp_path, hub, made_from):
    """A window fit holding a var and a window nonlinear autoencoder of 3 rows, and a
    window export of the autoencoder made from `made_from`. Returns how the autoencoder
    scores windows in torch."""
    model = WindowNonlinearAe(rows=3, k=4, hidden=8, arguments=FitArguments(
        epochs=1, batch=16, rate=1e-3, improvement=0.0, patience=1, seed=0))
    windows = np.random.default_rng(1).normal(size=(64, 3, len(SIGNALS)))
    tensors, score, _ = model.fit(windows.astype(np.float32))
    weights = {"scale.mean": torch.zeros(len(SIGNALS)),
               "scale.std": torch.ones(len(SIGNALS)), **tensors}
    monkeypatch.setattr(score_windows, "fetch_fitted_models", lambda *args: (
        weights, {"inputs": {"models": [{"model": "var", "rows": 3}, as_dict(model)]}}))
    net = model.network_with_weights(weights, len(SIGNALS))
    write_onnx_files([(model.onnx_name, net)], 3 * len(SIGNALS),
                     str(tmp_path / "window_onnx" / "20260101-000000"))
    hub.files = {"window_onnx/20260101-000000/meta.json": {
        "models": {"path": made_from}, "exported": [as_dict(model)]}}
    return model, score


def test_a_window_export_scores_its_models_alone_as_torch_does(tmp_path, hub,
                                                                monkeypatch):
    model, score = exported_window_ae(monkeypatch, tmp_path, hub,
                                      "window_models/20260101-000000")
    rows = moving_rows(6)
    monkeypatch.setattr(score_windows, "fetch_test_set", lambda *args: {
        "raw": rows, "seg": np.zeros(6), "min_speed": 5.0,
        "dataset": {name: DATASET[name] for name in ("test_set", "log_split", "grid")}})
    made = score_windows.main("u/d", REVISION, "test_sets/20260101-000000",
                              str(tmp_path), "u/runs", COMMIT,
                              "window_models/20260101-000000", str(tmp_path),
                              onnx_files="window_onnx/20260101-000000")

    scores, models, meta = score_windows.fetch_scores(made, str(tmp_path))
    assert models == [as_dict(model)], "the var is not exported, so it has no column"
    assert scores[2:, 0] == pytest.approx(
        score(np.stack([rows[end - 2:end + 1] for end in range(2, 6)])), abs=1e-5)
    assert meta["inputs"]["onnx_files"] == "window_onnx/20260101-000000"
    assert meta["onnx_files"]["precision"] == "float"
    assert "onnxruntime" in meta["versions"]


def test_a_window_export_needs_to_be_made_from_the_window_fit(tmp_path, hub,
                                                              monkeypatch):
    exported_window_ae(monkeypatch, tmp_path, hub, "window_models/20260102-000000")
    sets_over(monkeypatch)
    with pytest.raises(ValueError):
        score_windows.main("u/d", REVISION, "test_sets/20260101-000000",
                           str(tmp_path), "u/runs", COMMIT,
                           "window_models/20260101-000000", str(tmp_path),
                           onnx_files="window_onnx/20260101-000000")
