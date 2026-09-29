import json

import pytest

from evaluate import detection_table

REVISION = "ab" * 20
WHERE = {"repo": "u/d", "revision": REVISION}
INSTANT = {"model": "nonlinear ae", "k": 8, "hidden": 128, "epochs": 1000,
           "batch": 1024, "rate": 0.001, "improvement": 0.0001, "patience": 10,
           "seed": 3}
PCA = {"model": "pca", "k": 8}
WINDOW = {"model": "var", "rows": 20}


def caught(found, per_hour):
    """What an alarm caught at every k from 1 to 2, the same at each."""
    return {str(k): {"found": found, "found_worth_catching": found,
                     "alarms_per_hour": per_hour, "caught": []} for k in (1, 2)}


def a_test_run(fold, instant, found, per_hour=2.0):
    """A test run's files of the rules and `instant` on a replay test set at seed 0 of
    `fold`, the fold's own log split named."""
    return {
        "meta.json": {"test_set": dict(WHERE, path="test_sets/20260101-000000"),
                      "log_split": dict(WHERE, path=f"log_splits/20260101-00000{fold}"),
                      "attacks_worth_catching": 10},
        "detection.json": [{"detector": "rules", **caught(2, 1.0)},
                           {**instant, "threshold": 0.5, "false_positive_rate": 0.001,
                            **caught(found, per_hour)}]}


def window_test_run(test_run_path, found):
    return {"meta.json": {"test_run": {"repo": "u/runs", "revision": REVISION,
                                       "path": test_run_path}},
            "window_detection.json": [{"instant": {**INSTANT, "threshold": 0.5},
                                       "window": {**WINDOW, "threshold": 1.0},
                                       **caught(found, 2.0)}]}


def stand_in(hub, runs):
    """`runs` on the hub, `{path: {name: what the file holds}}`, and the test set and
    the log splits of folds 0 and 3 they name."""
    hub.files = {f"{path}/{name}": held for path, files in runs.items()
                 for name, held in files.items()}
    hub.files["test_sets/20260101-000000/meta.json"] = {
        "inputs": {"attack": "replay", "seed": 0}}
    for fold in (0, 3):
        hub.files[f"log_splits/20260101-00000{fold}/meta.json"] = {
            "inputs": {"fold": fold}}


def made(tmp_path, listed):
    path = tmp_path / "listed.json"
    path.write_text(json.dumps(listed))
    out = tmp_path / "table.md"
    detection_table.main("u/runs", REVISION, str(path), str(tmp_path / "local"),
                         str(tmp_path / "runs"), str(out))
    return out.read_text()


def one_fold(tmp_path, hub):
    """The table of the rules, the instant model, PCA and a var beside the instant
    model, on fold 3."""
    stand_in(hub, {"test_runs/20260101-000000": a_test_run(3, INSTANT, 5),
                   "test_runs/20260101-000001": a_test_run(3, PCA, 4),
                   "window_test_runs/20260101-000000": window_test_run(
                       "test_runs/20260101-000000", 7)})
    return made(tmp_path, {
        "test_runs": ["test_runs/20260101-000000", "test_runs/20260101-000001"],
        "window_test_runs": ["window_test_runs/20260101-000000"]})


def test_every_detector_gets_a_row_at_every_k(tmp_path, hub):
    table = one_fold(tmp_path, hub)
    assert "| detector | k=1 | k=2 |" in table
    assert "| rules | 2/10, 1.0/h | 2/10, 1.0/h |" in table
    assert "| rules + nonlinear ae h=128 k=8 | 5/10, 2.0/h | 5/10, 2.0/h |" in table
    assert "| rules + pca k=8 | 4/10, 2.0/h | 4/10, 2.0/h |" in table


def test_a_window_model_shows_what_it_adds_at_no_more_false_alarms(tmp_path, hub):
    table = one_fold(tmp_path, hub)
    assert "| rules + nonlinear ae h=128 k=8 + var r=20 | 7/10, 2.0/h, +2 |" in table


def test_the_table_records_what_it_was_made_from(tmp_path, hub):
    table = one_fold(tmp_path, hub)
    assert f"Read from `u/runs` at `{REVISION}`." in table
    assert '"window_test_runs/20260101-000000"' in table
    assert "### fold 3, replay, seed 0" in table


def test_the_folds_of_an_attack_are_summed_and_their_false_alarms_averaged(tmp_path,
                                                                           hub):
    stand_in(hub, {"test_runs/20260101-000000": a_test_run(3, INSTANT, 5, 2.0),
                   "test_runs/20260101-000001": a_test_run(0, INSTANT, 3, 4.0)})
    table = made(tmp_path, {"test_runs": ["test_runs/20260101-000000",
                                          "test_runs/20260101-000001"],
                            "window_test_runs": []})
    together = table.split("## Each run")[0]
    assert "Runs: fold 0 seed 0, fold 3 seed 0" in together
    assert "| rules + nonlinear ae h=128 k=8 | 8/20, 3.0/h | 8/20, 3.0/h |" in together


def test_a_detector_listed_twice_for_one_run_is_refused(tmp_path, hub):
    stand_in(hub, {"test_runs/20260101-000000": a_test_run(3, INSTANT, 5),
                   "test_runs/20260101-000001": a_test_run(3, INSTANT, 6)})
    with pytest.raises(ValueError, match="test_runs/20260101-000001"):
        made(tmp_path, {"test_runs": ["test_runs/20260101-000000",
                                      "test_runs/20260101-000001"],
                        "window_test_runs": []})
