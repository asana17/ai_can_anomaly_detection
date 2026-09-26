import json
import os

import numpy as np

from models import fit_windows
from models.fit import models_in, scale_for
from models.fit_windows import MODELS
from models.fits import Var
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
# row 4 is not a train row, and row 8 starts a new segment
TRAIN_ROWS = np.array([True] * 4 + [False] + [True] * 5)
SEG = np.array([0] * 8 + [1] * 2, np.int32)


def train_set(monkeypatch):
    """A stand-in train set of 10 grid rows, each row's first signal its index."""
    rng = np.random.default_rng(0)
    raw = rng.normal(size=(len(TRAIN_ROWS), len(SIGNALS))).astype(np.float32)
    raw[:, 0] = np.arange(len(raw))
    monkeypatch.setattr(fit_windows, "fetch_train_set", lambda *args: {
        "train": raw[TRAIN_ROWS], "raw": raw, "seg": SEG, "train_rows": TRAIN_ROWS,
        "min_speed": 5.0, "dataset": DATASET})
    return raw


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
    assert models_in(MODELS) == [Var(5), Var(10), Var(20)]


def test_windows_hold_train_rows_of_one_segment_oldest_first(tmp_path, monkeypatch):
    raw = train_set(monkeypatch)
    model = Kept(3)
    meta = fit_windows.write_models(str(tmp_path), [model], "u/d", REVISION,
                                    "train_sets/20260101-000000", str(tmp_path))

    scaled = scale_for(raw[TRAIN_ROWS]).apply(raw)
    assert np.array_equal(model.windows[0], scaled[[[0, 1, 2], [1, 2, 3], [5, 6, 7]]])
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
