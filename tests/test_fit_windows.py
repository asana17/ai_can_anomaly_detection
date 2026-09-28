import json
import os

import numpy as np

from models import fit_windows
from models.fit import models_in, scale_for
from models.fit_windows import MODELS
from models.fits import FitArguments, Var, WindowNonlinearAe
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20
DATASET = {"train_set": {"repo": "u/d", "revision": REVISION,
                         "path": "train_sets/20260101-000000"},
           "calibration_set": {"repo": "u/d", "revision": REVISION,
                               "path": "calibration_sets/20260101-000000"},
           "log_split": {"repo": "u/d", "revision": REVISION,
                         "path": "log_splits/20260101-000000"},
           "grid": {"repo": "u/d", "revision": REVISION,
                    "path": "grids/20260101-000000"}}
# 9 train rows. A row was taken out after the 4th, and the 8th starts a new segment.
SEG = np.array([0] * 4 + [1] * 3 + [2] * 2)


def train_set(monkeypatch):
    """A stand-in train set of moving rows."""
    rng = np.random.default_rng(0)
    train = rng.normal(size=(len(SEG), len(SIGNALS))).astype(np.float32)
    train[:, SIGNALS.index("wheel_speed")] = 10.0
    monkeypatch.setattr(fit_windows, "fetch_train_set", lambda *args: {
        "train": train, "seg": SEG, "min_speed": 5.0, "dataset": DATASET})
    return train


class Kept:
    """A window model that keeps the windows it is fitted on."""

    name = "kept"

    def __init__(self, rows):
        self.rows = rows
        self.windows = []

    def fit(self, windows):
        self.windows.append(windows)
        return {}, None, None


def test_the_models_beside_fit_windows_spread_into_one_model_per_value():
    arguments = FitArguments(epochs=1000, batch=1024, rate=0.001, improvement=0.0001,
                             patience=10, seed=3)
    assert models_in(MODELS) == [Var(5), Var(10), Var(20)] + [
        WindowNonlinearAe(rows, k, 128, arguments)
        for rows, k in ((5, 12), (5, 24), (10, 16), (10, 32), (20, 24), (20, 48))]


def test_windows_hold_train_rows_of_one_segment_oldest_first(tmp_path, monkeypatch):
    train = train_set(monkeypatch)
    model = Kept(3)
    meta = fit_windows.write_models(str(tmp_path), [model], "u/d", REVISION,
                                    "train_sets/20260101-000000", str(tmp_path))

    scaled = scale_for(train).apply(train)
    assert np.array_equal(model.windows[0], scaled[[[0, 1, 2], [1, 2, 3], [4, 5, 6]]])
    assert meta["windows"] == [3]


def test_a_run_keeps_the_weights_and_what_it_was_fitted_on(tmp_path, hub, monkeypatch):
    train_set(monkeypatch)
    monkeypatch.setattr(fit_windows, "models_in", lambda path: [Var(3)])
    made = fit_windows.main("u/d", REVISION, "train_sets/20260101-000000",
                            str(tmp_path), "u/runs", str(tmp_path))

    folder = tmp_path / made["path"]
    assert made["path"].startswith("window_models/")
    assert sorted(os.listdir(folder)) == ["losses.json", "meta.json",
                                          "weights.safetensors"]
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"train_set": "train_sets/20260101-000000",
                              "models": [{"model": "var", "rows": 3}]}
    assert meta["windows"] == [3]
    assert json.load(open(folder / "losses.json")) == [], "var is solved, not trained"


def test_a_run_keeps_the_losses_of_a_window_nonlinear_ae(tmp_path, hub, monkeypatch):
    train_set(monkeypatch)
    model = WindowNonlinearAe(3, 2, 8, FitArguments(epochs=2, batch=4, rate=1e-3,
                                           improvement=1e-4, patience=2, seed=0))
    monkeypatch.setattr(fit_windows, "models_in", lambda path: [Var(3), model])
    made = fit_windows.main("u/d", REVISION, "train_sets/20260101-000000",
                            str(tmp_path), "u/runs", str(tmp_path))

    folder = tmp_path / made["path"]
    losses = json.load(open(folder / "losses.json"))
    assert [entry["model"] for entry in losses] == ["window nonlinear ae"]
    assert len(losses[0]["losses"]) == 2


def test_a_window_holding_a_nan_is_not_fitted_on(tmp_path, monkeypatch):
    train = train_set(monkeypatch)
    train[5, 1] = np.nan
    model = Kept(3)
    meta = fit_windows.write_models(str(tmp_path), [model], "u/d", REVISION,
                                    "train_sets/20260101-000000", str(tmp_path))

    complete = np.delete(train, 5, axis=0)
    scaled = scale_for(complete).apply(train)
    # row 5 is in the window 4 to 6 alone, so the other two are kept
    assert np.array_equal(model.windows[0], scaled[[[0, 1, 2], [1, 2, 3]]])
    assert meta["windows"] == [2]


class KeptEvery(Kept):
    """A window model that keeps the windows it is fitted on, one every `stride` rows."""

    def __init__(self, rows, stride):
        super().__init__(rows)
        self.stride = stride


def test_a_model_with_a_stride_fits_on_one_window_every_stride_rows(
        tmp_path, monkeypatch):
    train = train_set(monkeypatch)
    model = KeptEvery(2, 2)
    meta = fit_windows.write_models(str(tmp_path), [model], "u/d", REVISION,
                                    "train_sets/20260101-000000", str(tmp_path))

    scaled = scale_for(train).apply(train)
    # each segment starts its count again, so 0-1 and 2-3, 4-5, and 7-8
    assert np.array_equal(model.windows[0], scaled[[[0, 1], [2, 3], [4, 5], [7, 8]]])
    assert meta["windows"] == [4]
