import json
import os

import numpy as np
import pytest
import torch

from deploy.export import write_onnx_files
from deploy.quantize import write_int8_files
from scoring import score
from models.autoencoder import NonlinearAutoencoder
from models.fits import FitArguments, NonlinearAe, as_dict
from models.onnx_files import onnx_name, onnx_residuals
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20
COMMIT = "de" * 20

WHEEL = SIGNALS.index("wheel_speed")
DATASET = {name: {"repo": "u/d", "revision": REVISION, "path": f"{name}s/20260101-000000"}
           for name in ("calibration_set", "log_split", "grid")}


def rows_at(speeds):
    """One row per speed, every other signal 0."""
    raw = np.zeros((len(speeds), len(SIGNALS)), np.float32)
    raw[:, WHEEL] = speeds
    return raw


def stand_in(monkeypatch, hub, raw, flagged, models=({"model": "pca", "k": 2},)):
    """A fit holding `models`, and a calibration set holding `raw` with `flagged` hit
    by a rule."""
    weights = {"scale.mean": torch.zeros(len(SIGNALS)),
               "scale.std": torch.ones(len(SIGNALS)),
               "pca.k2.centre": torch.zeros(len(SIGNALS)),
               "pca.k2.basis": torch.zeros(len(SIGNALS), 2)}
    monkeypatch.setattr(score, "fetch_fitted_models", lambda *args: (
        weights, {"inputs": {"models": list(models)}}))
    monkeypatch.setattr(score, "fetch_calibration_set", lambda *args: {
        "calibration": raw, "min_speed": 5.0, "dataset": DATASET})
    monkeypatch.setattr(score, "rule_hits", lambda raw, settings: flagged)
    hub.files = {}


def scored(tmp_path, **options):
    """Score the stand-in calibration set, and return its folder."""
    made = score.main("u/d", REVISION, "calibration_sets/20260101-000000", str(tmp_path),
                      "u/runs", COMMIT, "models/20260101-000000", str(tmp_path),
                      **options)
    return tmp_path / made["path"]


def test_a_row_at_or_below_the_speed_has_no_score(tmp_path, hub,
                                                                    monkeypatch):
    raw = rows_at([1.0, 5.0, 9.0, 20.0])
    stand_in(monkeypatch, hub, raw, np.array([True, False, True, False]))
    folder = scored(tmp_path)

    assert sorted(os.listdir(folder)) == ["meta.json", "models.json", "rule_hits.npy",
                                          "scores.npy"]
    scores = np.load(folder / "scores.npy")
    assert scores.shape == (4, 1), "a row of the set each, a column of a model each"
    assert np.isnan(scores[:, 0]).tolist() == [True, True, False, False], \
        "a row a rule hits is scored too"
    assert np.load(folder / "rule_hits.npy").tolist() == [False, False, True, False], \
        "a rule hit on a standing row is no hit"
    assert json.load(open(folder / "models.json")) == [{"model": "pca", "k": 2}]
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"set": "calibration_sets/20260101-000000",
                              "models": "models/20260101-000000", "onnx_files": None,
                              "precision": None}
    assert meta["rows"] == 4 and meta["scored"] == 2
    assert meta["calibration_set"] == DATASET["calibration_set"]


def int8_fit(monkeypatch, tmp_path, hub, raw):
    """A stand-in fit holding one nonlinear autoencoder, with its int8 file."""
    model = NonlinearAe(k=4, hidden=8, arguments=FitArguments(
        epochs=2, batch=16, rate=1e-3, improvement=1e-4, patience=2, seed=0))
    stand_in(monkeypatch, hub, raw, np.zeros(len(raw), bool), models=(as_dict(model),))
    torch.manual_seed(0)
    net = NonlinearAutoencoder(signals=len(SIGNALS), latent_dim=4, hidden=8)
    write_onnx_files([(onnx_name(model), net)], len(SIGNALS), str(tmp_path / "float"))
    write_int8_files([onnx_name(model)], str(tmp_path / "float"), raw,
                     str(tmp_path / "quantize" / "20260101-000000"), batch=16)
    return tmp_path / "quantize" / "20260101-000000" / f"{onnx_name(model)}_int8.onnx"


def test_onnx_files_score_as_themselves(tmp_path, hub, monkeypatch):
    raw = np.random.default_rng(0).normal(size=(64, len(SIGNALS))).astype(np.float32)
    raw[:, WHEEL] = 10.0
    int8_file = int8_fit(monkeypatch, tmp_path, hub, raw)
    hub.files = {"quantize/20260101-000000/meta.json": {
        "models": {"path": "models/20260101-000000"}}}
    folder = scored(tmp_path, onnx_files="quantize/20260101-000000", precision="int8")

    assert np.load(folder / "scores.npy")[:, 0] == pytest.approx(
        onnx_residuals(str(int8_file), raw))
    meta = json.load(open(folder / "meta.json"))
    assert meta["onnx_files"]["precision"] == "int8"
    assert "onnxruntime" in meta["versions"]


def test_onnx_files_need_to_be_made_from_the_fit(tmp_path, hub, monkeypatch):
    stand_in(monkeypatch, hub, rows_at([10.0]), np.zeros(1, bool))
    hub.files = {"quantize/20260101-000000/meta.json": {
        "models": {"path": "models/20260102-000000"}}}
    with pytest.raises(ValueError):
        scored(tmp_path, onnx_files="quantize/20260101-000000", precision="int8")
