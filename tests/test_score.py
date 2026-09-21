import json
import os

import numpy as np
import torch

from common.settings import Settings
from deploy.export import write_onnx_files
from deploy.quantize import write_int8_files
from detect.alarm import alarmed_rows
from evaluate.pc import score
from models.autoencoder import NonlinearAutoencoder
from models.fits import FitArguments, NonlinearAe, as_dict
from models.onnx_files import onnx_name
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20
COMMIT = "de" * 20

WHEEL = SIGNALS.index("wheel_speed")
MODEL = NonlinearAe(k=4, hidden=8, arguments=FitArguments(
    epochs=2, batch=16, rate=1e-3, improvement=1e-4, patience=2, seed=0))


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
    alarmed = alarmed_rows(flag.astype(float), 0.5, rows_to_score["rules"],
                           rows_to_score["seg"], need)
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


def stand_in(monkeypatch, hub):
    """A threshold, the model it belongs to, and six attacked rows to score it on."""
    where = {"repo": "u/runs", "revision": REVISION, "path": "models/20260101-000000"}
    hub.files = {
        "thresholds/20260101-000000/meta.json": {
            "inputs": {"models": "models/20260101-000000", "target": 0.001,
                       "onnx_files": None, "precision": None},
            "models": where, "onnx_files": None,
            "train_set": dict(where, repo="u/d", path="train_sets/20260101-000000")},
        "thresholds/20260101-000000/thresholds.json": [
            {"model": "pca", "k": 2, "threshold": 0.5}]}
    monkeypatch.setattr(score, "fetch_fitted_models", lambda *args: (
        {"scale.mean": torch.zeros(len(SIGNALS)), "scale.std": torch.ones(len(SIGNALS)),
         "pca.k2.centre": torch.zeros(len(SIGNALS)),
         "pca.k2.basis": torch.zeros(len(SIGNALS), 2)}, {}))

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
        "dataset": {"attack_set": {"repo": "u/d", "revision": REVISION,
                                   "path": "attack_sets/20260101-000000"},
                    "log_split": {"repo": "u/d", "revision": REVISION,
                                  "path": "log_splits/20260101-000000"},
                    "grid": {"repo": "u/d", "revision": REVISION,
                             "path": "grids/20260101-000000"}}})
    monkeypatch.setattr("evaluate.counting.rule_hits",
                        lambda raw, settings: np.zeros(len(raw), bool))


def test_every_model_is_scored_beside_the_rules(tmp_path, hub, monkeypatch):
    stand_in(monkeypatch, hub)
    made = score.main("u/d", REVISION, "attack_sets/20260101-000000", str(tmp_path),
                      "u/runs", COMMIT, "thresholds/20260101-000000", str(tmp_path))

    folder = tmp_path / made["path"]
    assert sorted(os.listdir(folder)) == ["attacks.json", "detection.json",
                                          "meta.json"]
    caught = json.load(open(folder / "detection.json"))
    assert [k.get("detector", k.get("model")) for k in caught] == ["rules", "pca"]
    assert caught[1]["threshold"] == 0.5, "the threshold comes from calibrate"
    kept = json.load(open(folder / "attacks.json"))
    assert len(kept) == 1 and kept[0]["moved"] > 0, "every attack keeps what it moved"

    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"attack_set": "attack_sets/20260101-000000",
                              "thresholds": "thresholds/20260101-000000",
                              "moved": Settings().MOVED,
                              "hold": list(Settings().HOLD)}
    assert meta["attacks"] == 1 and meta["attacks_scorable"] == 1
    assert meta["rows"] == 6


def int8_stand_in(monkeypatch, tmp_path, hub):
    """What `stand_in` holds, with the model a nonlinear autoencoder and its int8 file.

    The thresholds were taken with the int8 file.
    """
    stand_in(monkeypatch, hub)
    torch.manual_seed(0)
    net = NonlinearAutoencoder(signals=len(SIGNALS), latent_dim=4, hidden=8)
    rows = np.random.default_rng(0).normal(size=(64, len(SIGNALS))).astype(np.float32)
    write_onnx_files([(onnx_name(MODEL), net)], len(SIGNALS), str(tmp_path / "float"))
    write_int8_files([onnx_name(MODEL)], str(tmp_path / "float"), rows,
                     str(tmp_path / "quantize" / "20260101-000000"), batch=16)
    onnx_files = {"repo": "u/runs", "revision": REVISION,
                  "path": "quantize/20260101-000000", "precision": "int8"}
    hub.files["thresholds/20260101-000000/meta.json"].update(
        inputs={"models": "models/20260101-000000", "target": 0.001,
                "onnx_files": "quantize/20260101-000000", "precision": "int8"},
        onnx_files=onnx_files)
    hub.files.update({
        "thresholds/20260101-000000/thresholds.json": [
            {**as_dict(MODEL), "threshold": 0.25}],
        "quantize/20260101-000000/meta.json": {
            "inputs": {"onnx": "onnx/20260101-000000"}}})


def test_thresholds_taken_with_onnx_files_score_with_them(tmp_path, hub,
                                                            monkeypatch):
    int8_stand_in(monkeypatch, tmp_path, hub)
    made = score.main("u/d", REVISION, "attack_sets/20260101-000000", str(tmp_path),
                      "u/runs", COMMIT, "thresholds/20260101-000000", str(tmp_path))

    caught = json.load(open(tmp_path / made["path"] / "detection.json"))
    assert caught[1]["model"] == "nonlinear ae"
    assert caught[1]["threshold"] == 0.25
    meta = json.load(open(tmp_path / made["path"] / "meta.json"))
    assert meta["onnx_files"]["precision"] == "int8"
    assert "onnxruntime" in meta["versions"]
