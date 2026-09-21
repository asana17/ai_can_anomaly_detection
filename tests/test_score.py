import json
import os

import numpy as np
import torch

from assemble.scale import Scale
from common.settings import Settings
from evaluate.pc import score
from preprocess.features.signal_state import SIGNALS

WHEEL = SIGNALS.index("wheel_speed")


def a_test(scorable=np.array([True])):
    """Six rows, one attack over rows 1 and 2, four rows nothing flags."""
    rows_to_score = {"rules": np.zeros(6, bool),
                     "quiet": np.array([True, False, False, True, True, True]),
                     "seg": np.zeros(6, np.int32), "mv": np.ones(6, bool),
                     "hours": 2.0}
    attacks_to_check = {"injected": [{"first": 1, "last": 2}], "scorable": scorable}
    return rows_to_score, attacks_to_check


def caught(flag, rows_to_score, attacks_to_check, need=1):
    """What `flag` catches, as `score_models` counts it."""
    alarmed = score.alarming_rows(flag, rows_to_score, need)
    return {**score.attacks_caught(alarmed, attacks_to_check),
            "alarms_per_hour": score.false_alarm_rate(alarmed, rows_to_score)}


def test_what_a_flag_catches_and_what_it_costs():
    flag = np.array([False, True, False, False, True, False])

    got = caught(flag, *a_test())
    assert got["found"] == 1, "the attack has a flagged row"
    assert got["caught"] == [0], "and it is the first attack"
    assert got["alarms_per_hour"] == 0.5, "one alarm outside an attack, 2 hours"
    assert score.false_positive_rate(flag, a_test()[0]) == 0.25


def test_an_attack_that_moved_no_row_is_counted_apart():
    flag = np.array([False, True, False, False, False, False])

    got = caught(flag, *a_test(np.array([False])))
    assert got["found"] == 1 and got["found_scorable"] == 0


def stand_in(monkeypatch):
    """A threshold, the model it belongs to, and six attacked rows to score it on."""
    where = {"repo": "u/runs", "revision": "abc", "path": "models/t"}
    monkeypatch.setattr(score, "fetch_thresholds", lambda *args: (
        [{"model": "pca", "k": 2, "threshold": 0.5}],
        {"models": where, "train_set": dict(where, repo="u/d", path="train_sets/t")}))
    monkeypatch.setattr(score, "fetch_models", lambda *args: (
        {"pca.k2.centre": torch.zeros(len(SIGNALS)),
         "pca.k2.basis": torch.zeros(len(SIGNALS), 2)}, {}))
    monkeypatch.setattr(score, "fetch_scale", lambda *args: Scale(
        np.zeros(len(SIGNALS), np.float32), np.ones(len(SIGNALS), np.float32)))

    raw = np.zeros((6, len(SIGNALS)), np.float32)
    raw[:, WHEEL] = 10.0
    raw[1:3, 0] = 40.0                      # the rows the attack changed
    times = np.arange(6) * 0.1
    monkeypatch.setattr(score, "fetch_attack_set", lambda *args: {
        "raw": raw, "t": times, "seg": np.zeros(6, np.int32),
        "label": np.array([False, True, True, False, False, False]),
        "wheel": np.full(6, 10.0, np.float32),
        "attacks": [{"log": "a.csv", "first": 1, "last": 2}],
        "before": lambda log: {t: np.zeros(len(SIGNALS), np.float32) for t in times},
        "min_speed": 5.0,
        "dataset": {"attack_set": {"repo": "u/d", "revision": "abc",
                                   "path": "attack_sets/t"}}})
    monkeypatch.setattr("evaluate.counting.rule_hits",
                        lambda raw, settings: np.zeros(len(raw), bool))


def test_every_model_is_scored_beside_the_rules(tmp_path, hub, monkeypatch):
    stand_in(monkeypatch)
    made = score.main("u/d", "abc", "attack_sets/t", str(tmp_path), "u/runs", "def",
                      "thresholds/t", str(tmp_path))

    folder = tmp_path / made["path"]
    assert sorted(os.listdir(folder)) == ["attacks.json", "detection.json",
                                          "meta.json"]
    caught = json.load(open(folder / "detection.json"))
    assert [k.get("detector", k.get("model")) for k in caught] == ["rules", "pca"]
    assert caught[1]["threshold"] == 0.5, "the threshold comes from calibrate"
    kept = json.load(open(folder / "attacks.json"))
    assert len(kept) == 1 and kept[0]["moved"] > 0, "every attack keeps what it moved"

    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"attack_set": "attack_sets/t",
                              "thresholds": "thresholds/t",
                              "moved": Settings().MOVED,
                              "hold": list(Settings().HOLD)}
    assert meta["attacks"] == 1 and meta["attacks_scorable"] == 1
    assert meta["rows"] == 6


def test_the_same_attack_set_and_thresholds_are_not_scored_twice(tmp_path, hub,
                                                                 monkeypatch):
    stand_in(monkeypatch)
    hub.files = {"scores/20260101-000000/meta.json": {"inputs": {
        "attack_set": "attack_sets/t", "thresholds": "thresholds/t",
        "moved": Settings().MOVED, "hold": list(Settings().HOLD)}}}
    found = score.main("u/d", "abc", "attack_sets/t", str(tmp_path), "u/runs", "def",
                       "thresholds/t", str(tmp_path))

    assert found["path"] == "scores/20260101-000000" and hub.uploaded == []
