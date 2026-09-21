import json
import os

import numpy as np
import pytest
import torch

from common.settings import Settings
from detect.alarm import alarmed_rows
from evaluate.pc import run_test_set
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20
COMMIT = "de" * 20

WHEEL = SIGNALS.index("wheel_speed")
WHERE = {"repo": "u/d", "revision": REVISION}


def a_test(worth_catching=np.array([True])):
    """Six rows, one attack over rows 1 and 2, four rows nothing flags."""
    rows = run_test_set.AttackedRows(
        quiet=np.array([True, False, False, True, True, True]),
        rule_hit=np.zeros(6, bool), segment=np.zeros(6, np.int32), hours=2.0)
    attacks = run_test_set.InjectedAttacks(injected=[{"first": 1, "last": 2}],
                                           worth_catching=worth_catching)
    return rows, attacks


def caught(flag, rows, attacks, need=1):
    """What `flag` catches, as `detection_of_each_model` counts it."""
    alarmed = alarmed_rows(flag.astype(float), 0.5, rows.rule_hit, rows.segment, need)
    return {**run_test_set.attacks_caught_by_alarms(alarmed, attacks),
            "alarms_per_hour": run_test_set.false_alarms_per_hour(alarmed, rows)}


def test_what_a_flag_catches_and_what_it_costs():
    flag = np.array([False, True, False, False, True, False])

    got = caught(flag, *a_test())
    assert got["found"] == 1, "the attack has a flagged row"
    assert got["caught"] == [0], "and it is the first attack"
    assert got["alarms_per_hour"] == 0.5, "one alarm outside an attack, 2 hours"
    assert run_test_set.false_positive_rate(flag, a_test()[0]) == 0.25


def test_an_attack_that_moved_no_row_is_counted_apart():
    flag = np.array([False, True, False, False, False, False])

    got = caught(flag, *a_test(np.array([False])))
    assert got["found"] == 1 and got["found_worth_catching"] == 0


def stand_in(monkeypatch, hub, onnx_files=None):
    """The threshold of the one model that scored six attacked rows, and those scores.

    `score` is stood in for, so `onnx_files` only says what the thresholds were taken
    with.
    """
    models = {"repo": "u/runs", "revision": REVISION, "path": "models/20260101-000000"}
    scores = np.array([[np.nan], [1.0], [1.0], [0.0], [0.0], [0.0]], np.float32)
    hub.files = {
        "thresholds/20260101-000000/meta.json": {
            "models": models, "onnx_files": onnx_files},
        "thresholds/20260101-000000/thresholds.json": [
            {"model": "pca", "k": 2, "threshold": 0.5}],
        "scores/20260101-000000/meta.json": {
            "models": models, "onnx_files": onnx_files,
            "test_set": dict(WHERE, path="test_sets/20260101-000000")},
        "scores/20260101-000000/models.json": [{"model": "pca", "k": 2}],
        "scores/20260101-000000/scores.npy": scores,
        "scores/20260101-000000/rule_hits.npy": np.zeros(6, bool)}
    scored = []
    monkeypatch.setattr(run_test_set.score, "main", lambda *args, **options: (
        scored.append((args[2], args[6], options)) or
        {"repo": "u/runs", "revision": REVISION, "path": "scores/20260101-000000"}))
    monkeypatch.setattr(run_test_set, "fetch_fitted_models", lambda *args: (
        {"scale.mean": torch.zeros(len(SIGNALS)), "scale.std": torch.ones(len(SIGNALS))},
        {}))

    raw = np.zeros((6, len(SIGNALS)), np.float32)
    raw[:, WHEEL] = 10.0
    raw[1:3, 0] = 40.0                      # the rows the attack changed
    times = np.arange(6) * 0.1
    monkeypatch.setattr(run_test_set, "fetch_test_set", lambda *args: {
        "raw": raw, "t": times, "seg": np.zeros(6, np.int32),
        "label": np.array([False, True, True, False, False, False]),
        "wheel": np.full(6, 10.0, np.float32),
        "attacks": [{"log": "a.csv", "first": 1, "last": 2}],
        "before": lambda log: {t: np.zeros(len(SIGNALS), np.float32) for t in times},
        "min_speed": 5.0,
        "dataset": {name: dict(WHERE, path=f"{name}s/20260101-000000")
                    for name in ("test_set", "log_split", "grid")}})
    return scored


def run(tmp_path):
    """Run the stand-in test set at the stand-in threshold, and return its folder."""
    made = run_test_set.main("u/d", REVISION, "test_sets/20260101-000000", str(tmp_path),
                             "u/runs", COMMIT, "thresholds/20260101-000000",
                             str(tmp_path))
    return tmp_path / made["path"]


def test_every_model_is_counted_beside_the_rules(tmp_path, hub, monkeypatch):
    scored = stand_in(monkeypatch, hub)
    folder = run(tmp_path)

    assert scored == [("test_sets/20260101-000000", "models/20260101-000000",
                       {"onnx_files": None, "precision": None})], \
        "the test set is scored with the models the thresholds name"
    assert sorted(os.listdir(folder)) == ["attacks.json", "detection.json", "meta.json"]
    caught = json.load(open(folder / "detection.json"))
    assert [k.get("detector", k.get("model")) for k in caught] == ["rules", "pca"]
    assert caught[1]["threshold"] == 0.5, "the threshold comes from calibrate"
    assert caught[1]["1"]["caught"] == [0], "the scores over it catch the attack"
    kept = json.load(open(folder / "attacks.json"))
    assert len(kept) == 1 and kept[0]["moved"] > 0, "every attack keeps what it moved"

    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"test_set": "test_sets/20260101-000000",
                              "thresholds": "thresholds/20260101-000000",
                              "moved": Settings().MOVED,
                              "hold": list(Settings().HOLD)}
    assert meta["attacks"] == 1 and meta["attacks_worth_catching"] == 1
    assert meta["rows"] == 6


def test_the_test_set_is_scored_with_the_onnx_files_the_thresholds_name(tmp_path, hub,
                                                                       monkeypatch):
    onnx_files = {"repo": "u/runs", "revision": REVISION,
                  "path": "quantize/20260101-000000", "precision": "int8"}
    scored = stand_in(monkeypatch, hub, onnx_files=onnx_files)
    folder = run(tmp_path)

    assert scored[0][2] == {"onnx_files": "quantize/20260101-000000",
                            "precision": "int8"}
    assert json.load(open(folder / "meta.json"))["onnx_files"] == onnx_files


def test_a_model_with_no_threshold_is_refused(tmp_path, hub, monkeypatch):
    stand_in(monkeypatch, hub)
    hub.files["thresholds/20260101-000000/thresholds.json"] = [
        {"model": "pca", "k": 4, "threshold": 0.5}]
    with pytest.raises(ValueError):
        run(tmp_path)


def test_period_comes_from_the_commonest_step():
    times = np.array([0.0, 0.1, 0.2, 0.3, 30.0, 30.1])   # one recording gap
    assert abs(run_test_set.period_of(times) - 0.1) < 1e-9


def test_an_attack_is_measured_by_the_largest_change_it_made():
    clean = {0.0: np.zeros(3, np.float32), 0.1: np.zeros(3, np.float32)}
    attacked = {"before": lambda log: clean,
                "raw": np.array([[1.0, 0.0, 0.0], [0.0, 3.0, 0.0]], np.float32),
                "t": np.array([0.0, 0.1]), "label": np.array([True, True])}

    moved = run_test_set.z_distance_an_attack_moved({"log": "a.csv", "first": 0, "last": 1}, attacked,
                           np.ones(3, np.float32))
    assert moved == 3.0, "the row it moved furthest is the one that counts"


def test_a_row_the_attack_left_alone_is_not_measured():
    clean = {0.0: np.zeros(2, np.float32), 0.1: np.zeros(2, np.float32)}
    attacked = {"before": lambda log: clean,
                "raw": np.array([[9.0, 0.0], [0.0, 2.0]], np.float32),
                "t": np.array([0.0, 0.1]), "label": np.array([False, True])}

    moved = run_test_set.z_distance_an_attack_moved({"log": "a.csv", "first": 0, "last": 1}, attacked,
                           np.ones(2, np.float32))
    assert moved == 2.0
