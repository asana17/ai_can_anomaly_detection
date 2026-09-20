import json

import numpy as np
import pytest

from assemble import seconds
from common import hub_dirs
from preprocess.features.signal_state import SIGNALS


def _logs(tmp_path):
    data = tmp_path / "data" / "part_1"
    data.mkdir(parents=True)
    for name in ("a.csv", "b.csv"):
        (data / name).write_text("")
    return str(tmp_path / "data")


def test_it_measures_the_logs_named_under_data_dir(tmp_path, monkeypatch, hub):
    monkeypatch.setattr(seconds, "seconds_above",
                        lambda logs, **rest: {p: 1.0 for p in logs})
    made = seconds.main(_logs(tmp_path), "part_*/*.csv", str(tmp_path / "local"), "u/d")
    folder = tmp_path / "local" / made["path"]
    assert json.loads((folder / "seconds.json").read_text()) == {
        "part_1/a.csv": 1.0, "part_1/b.csv": 1.0}
    assert made["revision"] == "def" and hub.uploaded[0]["repo_type"] == "dataset"


def test_it_names_the_directory_built_from_the_same_logs(tmp_path, monkeypatch, hub):
    data = _logs(tmp_path)
    inputs = {"logs": seconds.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]),
              "count": 2, "min_speed": 5.0, "period": 0.1, "max_hold": 1.0}
    hub.files = {"seconds/20260101-000000/meta.json": {"inputs": inputs}}
    monkeypatch.setattr(seconds, "seconds_above", None)     # measuring would fail
    found = seconds.main(data, "part_*/*.csv", str(tmp_path / "local"), "u/d")
    assert found == {"repo": "u/d", "revision": "abc",
                     "path": "seconds/20260101-000000"}
    assert hub.uploaded == []


def test_rebuild_measures_them_again(tmp_path, monkeypatch, hub):
    data = _logs(tmp_path)
    inputs = {"logs": seconds.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]),
              "count": 2, "min_speed": 5.0, "period": 0.1, "max_hold": 1.0}
    hub.files = {"seconds/20260101-000000/meta.json": {"inputs": inputs}}
    monkeypatch.setattr(seconds, "seconds_above",
                        lambda logs, **rest: {p: 2.0 for p in logs})
    made = seconds.main(data, "part_*/*.csv", str(tmp_path / "local"), "u/d",
                        rebuild=True)
    assert made["path"] != "seconds/20260101-000000" and len(hub.uploaded) == 1


def test_find_matches_a_tuple_to_the_list_meta_json_holds(tmp_path, hub):
    hub.files = {"splits/20260101-000000/meta.json": {"inputs": {"hold": [1, 10]}}}
    found = hub_dirs.find("u/d", "splits", {"hold": (1, 10)}, str(tmp_path / "local"))
    assert found["path"] == "splits/20260101-000000"


def test_the_digest_changes_with_a_log_s_size(tmp_path):
    data = _logs(tmp_path)
    before = seconds.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"])
    (tmp_path / "data" / "part_1" / "a.csv").write_text("1")
    assert seconds.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]) != before


def test_seconds_above_counts_the_moving_rows_on_the_grid(monkeypatch):
    def grid_rows(logs, **rest):
        raw = np.zeros((4, len(SIGNALS)), np.float32)
        raw[:, SIGNALS.index("wheel_speed")] = [0.0, 4.0, 6.0, 80.0]
        return raw, np.arange(4) * 0.1, np.zeros(4, np.int32)

    monkeypatch.setattr(seconds, "grid_rows", grid_rows)
    got = seconds.seconds_above(["a.csv"], min_speed=5.0, period=0.1, max_hold=1.0)
    assert got == {"a.csv": pytest.approx(0.2)}      # two moving rows, 100 ms apart


def test_seconds_above_gives_a_log_with_no_row_0(monkeypatch):
    monkeypatch.setattr(seconds, "grid_rows", lambda logs, **rest: (
        np.zeros(0, np.float32), np.zeros(0), np.zeros(0, np.int32)))
    assert seconds.seconds_above(["a.csv"], min_speed=5.0, period=0.1, max_hold=1.0) == {"a.csv": 0.0}
