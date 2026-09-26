import json
import os

import numpy as np
import torch
from safetensors.torch import load_file

from models import fit
from models.fit import MODELS, models_in
from models.fits import Pca, as_dict
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20


def test_the_models_beside_fit_spread_into_one_model_per_value():
    listed = json.load(open(MODELS))
    models = models_in(MODELS)

    assert len(listed) == 1 and len(models) == 3
    assert [as_dict(model)["k"] for model in models] == listed[0]["k"]
    assert as_dict(models[0])["rate"] == listed[0]["rate"]


def train_set(monkeypatch, rows=8):
    """A stand-in train set of `rows` moving rows."""
    raw = np.zeros((rows, len(SIGNALS)), np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = np.arange(rows) + 10.0
    raw[:, 0] = np.arange(rows)
    monkeypatch.setattr(fit, "fetch_train_set", lambda *args: {
        "train": raw, "calibration": raw, "min_speed": 5.0,
        "dataset": {"train_set": {"repo": "u/d", "revision": REVISION,
                                  "path": "train_sets/20260101-000000"},
                    "calibration_set": {"repo": "u/d", "revision": REVISION,
                                        "path": "calibration_sets/20260101-000000"},
                    "log_split": {"repo": "u/d", "revision": REVISION,
                                  "path": "log_splits/20260101-000000"},
                    "grid": {"repo": "u/d", "revision": REVISION,
                             "path": "grids/20260101-000000"}}})
    monkeypatch.setattr(fit, "models_in", lambda path: [Pca(2)])
    return raw


def test_a_run_keeps_the_weights_the_losses_and_what_it_was_fitted_on(tmp_path, hub,
                                                                      monkeypatch):
    raw = train_set(monkeypatch)
    made = fit.main("u/d", REVISION, "train_sets/20260101-000000", str(tmp_path),
                    "u/runs", str(tmp_path))

    folder = tmp_path / made["path"]
    assert sorted(os.listdir(folder)) == ["losses.json", "meta.json",
                                          "weights.safetensors"]
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"train_set": "train_sets/20260101-000000",
                              "models": [{"model": "pca", "k": 2}]}
    assert meta["rows"] == len(raw) and meta["train_set"]["revision"] == REVISION
    assert json.load(open(folder / "losses.json")) == [], "pca is solved, not trained"
    assert hub.uploaded[0]["path_in_repo"] == made["path"]


def test_a_row_holding_a_nan_is_not_fitted_on(tmp_path, hub, monkeypatch):
    raw = train_set(monkeypatch)
    raw[3, 1] = np.nan
    made = fit.main("u/d", REVISION, "train_sets/20260101-000000", str(tmp_path),
                    "u/runs", str(tmp_path))

    meta = json.load(open(tmp_path / made["path"] / "meta.json"))
    assert meta["rows"] == len(raw) - 1
    weights = load_file(tmp_path / made["path"] / "weights.safetensors")
    assert all(torch.isfinite(tensor).all() for tensor in weights.values())
