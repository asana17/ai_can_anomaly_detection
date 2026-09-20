import json
import os

import numpy as np
import pytest
import torch

from assemble.scale import Scale
from evaluate import calibrate
from common.settings import Settings
from preprocess.features.signal_state import SIGNALS

WHEEL = SIGNALS.index("wheel_speed")
TRAIN_SET = {"repo": "u/d", "revision": "abc", "path": "train_sets/t"}


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


def run_and_train_set(monkeypatch, raw):
    """A stand-in run holding one PCA, fitted on a train set whose rows are `raw`."""
    weights = {"pca.k2.centre": torch.zeros(len(SIGNALS)),
               "pca.k2.basis": torch.zeros(len(SIGNALS), 2)}
    where = {"repo": "u/d", "revision": "abc", "path": "train_sets/t"}
    meta = {"inputs": {"train_set": "train_sets/t",
                       "models": [{"model": "pca", "k": 2}]},
            "train_set": where, "split": dict(where, path="splits/s"),
            "grid": dict(where, path="grids/g"), "min_speed": 5.0}
    monkeypatch.setattr(calibrate, "fetch_models", lambda *args: (weights, meta))
    stand_in(monkeypatch, raw, np.zeros(len(raw), bool))


def test_a_threshold_is_kept_for_every_model_of_the_run(tmp_path, hub, monkeypatch):
    raw = rows_at(np.arange(20) + 10.0)
    run_and_train_set(monkeypatch, raw)
    made = calibrate.main("u/runs", "def", "models/t", str(tmp_path), str(tmp_path))

    folder = tmp_path / made["path"]
    assert sorted(os.listdir(folder)) == ["meta.json", "thresholds.json"]
    kept = json.load(open(folder / "thresholds.json"))
    assert [k["model"] for k in kept] == ["pca"] and kept[0]["threshold"] > 0
    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"models": "models/t", "target": Settings().TARGET}
    assert meta["models"]["revision"] == "def" and meta["rows"] == len(raw)


def test_the_same_run_and_target_are_not_read_twice(tmp_path, hub, monkeypatch):
    run_and_train_set(monkeypatch, rows_at([10.0, 20.0]))
    hub.files = {"thresholds/20260101-000000/meta.json": {
        "inputs": {"models": "models/t", "target": Settings().TARGET}}}
    found = calibrate.main("u/runs", "def", "models/t", str(tmp_path), str(tmp_path))

    assert found["path"] == "thresholds/20260101-000000" and hub.uploaded == []
