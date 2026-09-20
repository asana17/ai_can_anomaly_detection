import json

import numpy as np
import pytest

from assemble import grid
from common import hub_dirs
from preprocess.features.signal_state import SIGNALS


def _logs(tmp_path):
    data = tmp_path / "data" / "part_1"
    data.mkdir(parents=True)
    for name in ("a.csv", "b.csv"):
        (data / name).write_text("")
    return str(tmp_path / "data")


def test_it_writes_the_rows_of_every_log_named_under_data_dir(tmp_path, monkeypatch,
                                                              hub):
    monkeypatch.setattr(grid, "rows_of_each",
                        lambda logs, **rest: [(p, [(0.0, [0.0] * len(SIGNALS)),
                                                   (0.1, [1.0] * len(SIGNALS))])
                                              for p in logs])
    made = grid.main(_logs(tmp_path), "part_*/*.csv", str(tmp_path / "local"), "u/d")
    folder = tmp_path / "local" / made["path"]
    assert np.load(folder / "grid_raw.npy").shape == (4, len(SIGNALS))
    assert json.loads((folder / "logs.json").read_text()) == {
        "logs": ["part_1/a.csv", "part_1/b.csv"], "rows": [2, 2]}
    assert made["revision"] == "def" and hub.uploaded[0]["repo_type"] == "dataset"


def test_each_log_starts_its_own_segment(tmp_path, monkeypatch, hub):
    monkeypatch.setattr(grid, "rows_of_each",
                        lambda logs, **rest: [(p, [(0.0, [0.0] * len(SIGNALS)),
                                                   (0.1, [1.0] * len(SIGNALS))])
                                              for p in logs])
    made = grid.main(_logs(tmp_path), "part_*/*.csv", str(tmp_path / "local"), "u/d")
    seg = np.load(tmp_path / "local" / made["path"] / "grid_seg.npy")
    assert seg.tolist() == [0, 0, 1, 1]


def test_it_names_the_directory_built_from_the_same_logs(tmp_path, monkeypatch, hub):
    data = _logs(tmp_path)
    inputs = {"logs": grid.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]),
              "count": 2, "period": 0.1, "max_hold": 1.0}
    hub.files = {"grids/20260101-000000/meta.json": {"inputs": inputs}}
    monkeypatch.setattr(grid, "write_grid", None)           # building would fail
    found = grid.main(data, "part_*/*.csv", str(tmp_path / "local"), "u/d")
    assert found == {"repo": "u/d", "revision": "abc",
                     "path": "grids/20260101-000000"}
    assert hub.uploaded == []


def test_rebuild_builds_them_again(tmp_path, monkeypatch, hub):
    data = _logs(tmp_path)
    inputs = {"logs": grid.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]),
              "count": 2, "period": 0.1, "max_hold": 1.0}
    hub.files = {"grids/20260101-000000/meta.json": {"inputs": inputs}}
    monkeypatch.setattr(grid, "rows_of_each",
                        lambda logs, **rest: [(p, [(0.0, [0.0] * len(SIGNALS))])
                                              for p in logs])
    made = grid.main(data, "part_*/*.csv", str(tmp_path / "local"), "u/d",
                     rebuild=True)
    assert made["path"] != "grids/20260101-000000" and len(hub.uploaded) == 1


def test_find_matches_a_tuple_to_the_list_meta_json_holds(tmp_path, hub):
    hub.files = {"splits/20260101-000000/meta.json": {"inputs": {"hold": [1, 10]}}}
    found = hub_dirs.find("u/d", "splits", {"hold": (1, 10)}, str(tmp_path / "local"))
    assert found["path"] == "splits/20260101-000000"


def test_the_digest_changes_with_a_log_s_size(tmp_path):
    data = _logs(tmp_path)
    before = grid.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"])
    (tmp_path / "data" / "part_1" / "a.csv").write_text("1")
    assert grid.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]) != before
