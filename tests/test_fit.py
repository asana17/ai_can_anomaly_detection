import json
import os

import numpy as np

from assemble.scale import Scale
from evaluate import fit
from evaluate.fit import MODELS, models_in
from models.fits import Pca, as_dict
from preprocess.features.signal_state import SIGNALS


def test_the_models_beside_fit_spread_into_one_model_per_value():
    listed = json.load(open(MODELS))
    models = models_in(MODELS)

    assert len(listed) == 3 and len(models) == 40
    assert as_dict(models[0]) == {"model": "pca", "k": 2}, "pca is fitted, not trained"
    assert as_dict(models[8])["rate"] == listed[1]["rate"]


def train_set(monkeypatch, rows=8):
    """A stand-in train set of `rows` moving rows, with a scale that changes nothing."""
    raw = np.zeros((rows, len(SIGNALS)), np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = np.arange(rows) + 10.0
    raw[:, 0] = np.arange(rows)
    monkeypatch.setattr(fit, "fetch_train_set", lambda *args: {
        "train": raw, "calibration": raw, "min_speed": 5.0,
        "scale": Scale(np.zeros(len(SIGNALS), np.float32),
                       np.ones(len(SIGNALS), np.float32)),
        "dataset": {"train_set": {"repo": "u/d", "revision": "abc",
                                  "path": "train_sets/t"}}})
    monkeypatch.setattr(fit, "models_in", lambda path: [Pca(2)])
    return raw


def test_a_run_keeps_the_weights_the_losses_and_what_it_was_fitted_on(tmp_path, hub,
                                                                      monkeypatch):
    raw = train_set(monkeypatch)
    made = fit.main("u/d", "abc", "train_sets/t", str(tmp_path), "u/runs", str(tmp_path))

    folder = tmp_path / made["path"]
    assert sorted(os.listdir(folder)) == ["losses.json", "meta.json",
                                          "weights.safetensors"]
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"train_set": "train_sets/t",
                              "models": [{"model": "pca", "k": 2}]}
    assert meta["rows"] == len(raw) and meta["train_set"]["revision"] == "abc"
    assert json.load(open(folder / "losses.json")) == [], "pca is solved, not trained"
    assert hub.uploaded[0]["path_in_repo"] == made["path"]


def test_a_run_of_the_same_inputs_is_not_fitted_again(tmp_path, hub, monkeypatch):
    train_set(monkeypatch)
    hub.files = {"models/20260101-000000/meta.json": {
        "inputs": {"train_set": "train_sets/t", "models": [{"model": "pca", "k": 2}]}}}
    found = fit.main("u/d", "abc", "train_sets/t", str(tmp_path), "u/runs",
                     str(tmp_path))

    assert found["path"] == "models/20260101-000000" and hub.uploaded == []
