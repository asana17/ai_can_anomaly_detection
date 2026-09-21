import json
import os

import numpy as np
import pytest
import torch

from assemble.scale import Scale
from deploy.export import write_onnx_files
from deploy.quantize import write_int8_files
from evaluate import calibrate
from common.settings import Settings
from models.autoencoder import NonlinearAutoencoder
from models.fits import FitArguments, NonlinearAe, as_dict
from models.onnx_files import onnx_name, onnx_residuals
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20
COMMIT = "de" * 20

WHEEL = SIGNALS.index("wheel_speed")
TRAIN_SET = {"repo": "u/d", "revision": REVISION, "path": "train_sets/20260101-000000"}


def rows_at(speeds):
    """One row per speed, every other signal 0."""
    raw = np.zeros((len(speeds), len(SIGNALS)), np.float32)
    raw[:, WHEEL] = speeds
    return raw


def stand_in(monkeypatch, raw, flagged):
    """A train set holding `raw` as its calibration rows, with `flagged` ruled out."""
    monkeypatch.setattr(calibrate, "fetch_train_set", lambda *args: {
        "calibration": raw, "min_speed": 5.0,
        "scale": Scale(np.zeros(len(SIGNALS), np.float32),
                       np.ones(len(SIGNALS), np.float32)), "dataset": {}})
    monkeypatch.setattr(calibrate, "rule_hits", lambda raw, settings: flagged)


def test_the_quantile_leaves_that_share_of_the_scores_above_it():
    scores = np.arange(1000, dtype=float)
    assert (scores > calibrate.quantile(scores, 0.1)).mean() == pytest.approx(0.1, 0.01)


def test_a_row_at_or_below_the_speed_sets_no_threshold(monkeypatch):
    raw = rows_at([1.0, 5.0, 9.0])
    stand_in(monkeypatch, raw, np.zeros(len(raw), bool))
    rows = calibrate.calibration_rows(calibrate.fetch_train_set(), Settings())

    assert rows[:, WHEEL].tolist() == [9.0]


def test_a_row_a_rule_flags_sets_no_threshold(monkeypatch):
    raw = rows_at([9.0, 20.0])
    stand_in(monkeypatch, raw, np.array([True, False]))
    rows = calibrate.calibration_rows(calibrate.fetch_train_set(), Settings())

    assert rows[:, WHEEL].tolist() == [20.0]


def run_and_train_set(monkeypatch, raw, models=({"model": "pca", "k": 2},)):
    """A stand-in run holding `models`, fitted on a train set whose rows are `raw`."""
    weights = {"scale.mean": torch.zeros(len(SIGNALS)),
               "pca.k2.centre": torch.zeros(len(SIGNALS)),
               "pca.k2.basis": torch.zeros(len(SIGNALS), 2)}
    where = {"repo": "u/d", "revision": REVISION, "path": "train_sets/20260101-000000"}
    meta = {"inputs": {"train_set": "train_sets/20260101-000000",
                       "models": list(models)},
            "train_set": where, "split": dict(where, path="splits/20260101-000000"),
            "grid": dict(where, path="grids/20260101-000000"), "min_speed": 5.0}
    monkeypatch.setattr(calibrate, "fetch_fitted_models", lambda *args: (weights, meta))
    stand_in(monkeypatch, raw, np.zeros(len(raw), bool))


def test_a_threshold_is_kept_for_every_model_of_the_run(tmp_path, hub, monkeypatch):
    raw = rows_at(np.arange(20) + 10.0)
    run_and_train_set(monkeypatch, raw)
    made = calibrate.main("u/runs", COMMIT, "models/20260101-000000", str(tmp_path),
                          str(tmp_path))

    folder = tmp_path / made["path"]
    assert sorted(os.listdir(folder)) == ["meta.json", "thresholds.json"]
    kept = json.load(open(folder / "thresholds.json"))
    assert [k["model"] for k in kept] == ["pca"] and kept[0]["threshold"] > 0
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"models": "models/20260101-000000",
                              "target": Settings().TARGET, "onnx_files": None,
                              "precision": None}
    assert meta["models"]["revision"] == COMMIT and meta["rows"] == len(raw)


def int8_run(monkeypatch, tmp_path, hub, raw):
    """A stand-in run holding one nonlinear autoencoder, with its int8 file."""
    model = NonlinearAe(k=4, hidden=8, arguments=FitArguments(
        epochs=2, batch=16, rate=1e-3, improvement=1e-4, patience=2, seed=0))
    run_and_train_set(monkeypatch, raw, models=(as_dict(model),))
    torch.manual_seed(0)
    net = NonlinearAutoencoder(signals=len(SIGNALS), latent_dim=4, hidden=8)
    write_onnx_files([(onnx_name(model), net)], len(SIGNALS), str(tmp_path / "float"))
    write_int8_files([onnx_name(model)], str(tmp_path / "float"), raw,
                     str(tmp_path / "quantize" / "20260101-000000"), batch=16)
    hub.files = {"quantize/20260101-000000/meta.json": {
        "inputs": {"onnx": "onnx/20260101-000000"},
        "models": {"path": "models/20260101-000000"}}}
    return tmp_path / "quantize" / "20260101-000000" / f"{onnx_name(model)}_int8.onnx"


def test_onnx_thresholds_come_from_the_onnx_files(tmp_path, hub, monkeypatch):
    raw = np.random.default_rng(0).normal(size=(64, len(SIGNALS))).astype(np.float32)
    raw[:, WHEEL] = 10.0
    int8_file = int8_run(monkeypatch, tmp_path, hub, raw)
    made = calibrate.main("u/runs", COMMIT, "models/20260101-000000", str(tmp_path),
                          str(tmp_path), onnx_files="quantize/20260101-000000",
                          precision="int8")

    kept = json.load(open(tmp_path / made["path"] / "thresholds.json"))
    scores = onnx_residuals(str(int8_file), raw)
    assert kept[0]["threshold"] == calibrate.quantile(scores, Settings().TARGET)
    meta = json.load(open(tmp_path / made["path"] / "meta.json"))
    assert meta["inputs"]["onnx_files"] == "quantize/20260101-000000"
    assert meta["inputs"]["precision"] == "int8"
    assert meta["onnx_files"]["precision"] == "int8"


def test_onnx_files_need_to_be_made_from_the_fit(tmp_path, hub,
                                                            monkeypatch):
    raw = rows_at(np.arange(20) + 10.0)
    run_and_train_set(monkeypatch, raw)
    hub.files = {"quantize/20260101-000000/meta.json": {
        "inputs": {"onnx": "onnx/20260102-000000"},
        "models": {"path": "models/20260102-000000"}}}
    with pytest.raises(ValueError):
        calibrate.main("u/runs", COMMIT, "models/20260101-000000", str(tmp_path),
                       str(tmp_path), onnx_files="quantize/20260101-000000",
                       precision="int8")
