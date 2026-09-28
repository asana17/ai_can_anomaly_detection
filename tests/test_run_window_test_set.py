import json

import numpy as np
import pytest
import torch

from evaluate import run_test_set_common, run_window_test_set
from evaluate.run_test_set_common import AttackedRows, InjectedAttacks
from preprocess.features.signal_state import SIGNALS

REVISION = "ab" * 20
WHERE = {"repo": "u/d", "revision": REVISION}
INSTANT = {"model": "nonlinear ae", "k": 8, "hidden": 128, "epochs": 1000,
           "batch": 1024, "rate": 0.001, "improvement": 0.0001, "patience": 10,
           "seed": 3}
WINDOW = {"model": "var", "rows": 5}


def twenty_rows():
    """Twenty moving rows in one segment, one attack over rows 10 and 11, 18 rows of
    0.1 s with no attack."""
    rows = AttackedRows(normal_moving=np.ones(20, bool), rule_hit=np.zeros(20, bool),
                        segment=np.zeros(20, np.int32), hours=18 * 0.1 / 3600)
    attacks = InjectedAttacks(injected=[{"first": 10, "last": 11}],
                              worth_catching=np.array([True]))
    return rows, attacks


def score_on(*at):
    """A score of 1 on the rows `at`, 0 elsewhere."""
    scores = np.zeros(20)
    scores[list(at)] = 1.0
    return scores


def counted(scores, window_scores, n=3):
    """What the instant model caught with a window model of 5 rows, both at a
    threshold of 0.5."""
    return run_window_test_set.detection_of_one_window_model(
        scores, 0.5, window_scores, 0.5, 5, *twenty_rows(), n)


def test_the_window_model_adds_the_rows_it_is_judged_at():
    kept = counted(score_on(2), score_on(11, 16))
    assert list(kept) == ["1", "2", "3"]
    assert kept["1"]["caught"] == [0], "the window ending at row 11"
    assert kept["1"]["alarms_per_hour"] == 4000.0, \
        "rows 2 to 4 and row 16 are two alarms in 18 rows of 0.1 s"


def test_the_window_model_alarms_only_at_k_of_the_last_n_rows():
    kept = counted(score_on(), score_on(11))
    assert kept["1"]["caught"] == [0]
    assert kept["2"]["found"] == 0, "row 11 alone is under 2 of 3"
    assert counted(score_on(), score_on(10, 11))["2"]["caught"] == [0]


def test_the_window_model_counts_again_when_the_segment_changes():
    rows, attacks = twenty_rows()
    rows.segment[10:] = 1
    kept = run_window_test_set.detection_of_one_window_model(
        score_on(), 0.5, score_on(9, 10), 0.5, 5, rows, attacks, 3)
    assert kept["2"]["found"] == 0, "row 9 is in the segment before row 10"
    assert counted(score_on(), score_on(9, 10))["2"]["caught"] == [0]


def test_a_window_that_holds_an_attack_catches_it_after_the_attack_ended():
    kept = counted(score_on(), score_on(15))    # the window holds rows 11 to 15
    assert kept["1"]["caught"] == [0]
    assert kept["1"]["alarms_per_hour"] == 0.0


def test_a_window_that_holds_no_row_of_an_attack_is_a_false_positive():
    kept = counted(score_on(), score_on(16))    # the window holds rows 12 to 16
    assert kept["1"]["found"] == 0
    assert kept["1"]["alarms_per_hour"] == 2000.0, "one alarm in 18 rows of 0.1 s"


def test_the_instant_model_catches_an_attack_only_inside_it():
    kept = counted(score_on(13), score_on())
    assert kept["1"]["found"] == 0
    assert kept["1"]["alarms_per_hour"] == 2000.0


def test_a_row_where_no_window_ends_does_not_alarm():
    window_scores = np.full(20, np.nan)
    assert counted(score_on(), window_scores)["1"]["found"] == 0


def test_each_window_model_is_counted_at_its_own_threshold():
    rows, attacks = twenty_rows()
    instant = [{"model": "nonlinear ae", "k": 8}, {"model": "nonlinear ae", "k": 4}]
    windows = [{"model": "var", "rows": 5}, {"model": "var", "rows": 10}]
    window_scores = np.stack([score_on(11), 1.5 * score_on(11)], axis=1)
    kept = run_window_test_set.detection_of_each_window_model(
        [{**instant[1], "threshold": 2.0}, {**instant[0], "threshold": 0.5}],
        instant, np.stack([score_on(10), score_on(10)], axis=1),
        [{**windows[1], "threshold": 2.0}, {**windows[0], "threshold": 0.5}],
        windows, window_scores, rows, attacks, 3)

    assert [(k["instant"]["k"], k["window"]["rows"]) for k in kept] == [
        (8, 5), (8, 10), (4, 5), (4, 10)]
    assert [(k["instant"]["threshold"], k["window"]["threshold"]) for k in kept] == [
        (0.5, 0.5), (0.5, 2.0), (2.0, 0.5), (2.0, 2.0)]
    assert [k["1"]["found"] for k in kept] == [1, 1, 1, 0], \
        "k 4 and the second window model are each under their own threshold"


def stand_in(monkeypatch, hub, window_onnx_files=None):
    """The rows of `twenty_rows` as a test run and window thresholds on the hub, the
    window thresholds taken as `window_onnx_files`, in torch when None.

    The instant model scores 1 on row 2, the window model on row 11. The attack moved
    row 10 by 40 on a scale of 1.
    """
    def at(path):
        return {"repo": "u/runs", "revision": REVISION, "path": path}

    dataset = {name: dict(WHERE, path=f"{name}s/20260101-000000")
               for name in ("test_set", "log_split", "grid")}
    hub.files = {
        "test_runs/20260101-000000/meta.json": {
            "inputs": {"moved": 1.0, "n": 3}, "scores": at("scores/20260101-000000"),
            "thresholds": at("thresholds/20260101-000000"),
            "models": at("models/20260101-000000"), "onnx_files": None, **dataset,
            "min_speed": 5.0, "rows": 20, "attacks": 1, "attacks_worth_catching": 1,
            "hours": 18 * 0.1 / 3600},
        "scores/20260101-000000/meta.json": {},
        "scores/20260101-000000/models.json": [INSTANT],
        "scores/20260101-000000/scores.npy": score_on(2)[:, None].astype(np.float32),
        "scores/20260101-000000/rule_hits.npy": np.zeros(20, bool),
        "thresholds/20260101-000000/meta.json": {},
        "thresholds/20260101-000000/thresholds.json": [{**INSTANT, "threshold": 0.5}],
        "window_thresholds/20260101-000000/meta.json": {
            "models": at("window_models/20260101-000000"),
            "onnx_files": window_onnx_files and {**at(window_onnx_files),
                                                 "precision": "float"}},
        "window_thresholds/20260101-000000/thresholds.json": [
            {**WINDOW, "threshold": 0.5}],
        "window_scores/20260101-000000/meta.json": {},
        "window_scores/20260101-000000/models.json": [WINDOW],
        "window_scores/20260101-000000/scores.npy":
            score_on(11)[:, None].astype(np.float32)}
    scored = []
    monkeypatch.setattr(run_window_test_set.score_windows, "main",
                        lambda *args, rebuild, onnx_files: (
                            scored.append((args[2], args[6], onnx_files, rebuild))
                            or at("window_scores/20260101-000000")))
    scale = {"scale.mean": torch.zeros(len(SIGNALS)),
             "scale.std": torch.ones(len(SIGNALS))}
    monkeypatch.setattr(run_test_set_common, "fetch_fitted_models",
                        lambda *args: (scale, {}))
    raw = np.zeros((20, len(SIGNALS)), np.float32)
    raw[:, SIGNALS.index("wheel_speed")] = 10.0
    raw[10, 0] = 40.0                       # the row the attack changed
    label = np.zeros(20, bool)
    label[10:12] = True
    times = np.arange(20) * 0.1
    monkeypatch.setattr(run_window_test_set, "fetch_test_set", lambda *args: {
        "raw": raw, "t": times, "seg": np.zeros(20, np.int32), "label": label,
        "wheel": np.full(20, 10.0, np.float32),
        "attacks": [{"log": "a.csv", "first": 10, "last": 11}],
        "before": lambda log: {t: raw[i] * (i != 10) for i, t in enumerate(times)},
        "min_speed": 5.0, "period": 0.1, "dataset": dataset})
    return scored


def run(tmp_path, rebuild=False):
    made = run_window_test_set.main("u/runs", REVISION, "test_runs/20260101-000000",
                                    REVISION, "window_thresholds/20260101-000000",
                                    str(tmp_path), str(tmp_path), rebuild=rebuild)
    return tmp_path / made["path"]


def test_the_test_set_is_counted_with_each_window_model(tmp_path, hub, monkeypatch):
    scored = stand_in(monkeypatch, hub)
    folder = run(tmp_path)

    assert scored == [("test_sets/20260101-000000", "window_models/20260101-000000",
                       None, False)], \
        "the test set's windows are scored with the models the thresholds name"
    kept = json.load(open(folder / "window_detection.json"))
    assert len(kept) == 1
    assert kept[0]["instant"] == {**INSTANT, "threshold": 0.5}
    assert kept[0]["window"] == {**WINDOW, "threshold": 0.5}
    assert [k for k in kept[0] if k.isdigit()] == ["1", "2", "3"], "k up to the run's n"
    assert kept[0]["1"]["found_worth_catching"] == 1, \
        "the attack moved a row by 40, so it is worth catching"

    meta = json.load(open(folder / "meta.json"))
    assert meta["inputs"] == {"test_run": "test_runs/20260101-000000",
                              "window_thresholds": "window_thresholds/20260101-000000"}


def test_the_windows_score_with_the_onnx_files_the_thresholds_came_from(
        tmp_path, hub, monkeypatch):
    scored = stand_in(monkeypatch, hub, window_onnx_files="window_onnx/20260101-000000")
    folder = run(tmp_path)

    assert scored[0][2] == "window_onnx/20260101-000000"
    meta = json.load(open(folder / "meta.json"))
    assert meta["window_onnx_files"]["path"] == "window_onnx/20260101-000000"


def test_a_rebuild_scores_the_test_set_s_windows_again(tmp_path, hub, monkeypatch):
    scored = stand_in(monkeypatch, hub)
    run(tmp_path, rebuild=True)

    assert scored[0][3] is True


def test_a_window_model_with_no_threshold_is_refused(tmp_path, hub, monkeypatch):
    stand_in(monkeypatch, hub)
    hub.files["window_thresholds/20260101-000000/thresholds.json"] = [
        {"model": "var", "rows": 10, "threshold": 0.5}]
    with pytest.raises(ValueError):
        run(tmp_path)
