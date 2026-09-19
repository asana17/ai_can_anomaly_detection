import json

from assemble import seconds
from common import hub_dirs


def _logs(tmp_path):
    data = tmp_path / "data" / "part_1"
    data.mkdir(parents=True)
    for name in ("a.csv", "b.csv"):
        (data / name).write_text("")
    return str(tmp_path / "data")


def test_it_measures_the_logs_named_under_data_dir(tmp_path, monkeypatch, hub):
    monkeypatch.setattr(seconds, "seconds_above",
                        lambda logs, min_speed: {p: 1.0 for p in logs})
    made = seconds.main(_logs(tmp_path), "part_*/*.csv", str(tmp_path / "local"), "u/d")
    folder = tmp_path / "local" / made["path"]
    assert json.loads((folder / "seconds.json").read_text()) == {
        "part_1/a.csv": 1.0, "part_1/b.csv": 1.0}
    assert made["revision"] == "def" and hub.uploaded[0]["repo_type"] == "dataset"


def test_it_names_the_directory_built_from_the_same_logs(tmp_path, monkeypatch, hub):
    data = _logs(tmp_path)
    inputs = {"logs": seconds.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]),
              "count": 2, "min_speed": 5.0}
    hub.files = {"seconds/20260101-000000/meta.json": {"inputs": inputs}}
    monkeypatch.setattr(seconds, "seconds_above", None)     # measuring would fail
    found = seconds.main(data, "part_*/*.csv", str(tmp_path / "local"), "u/d")
    assert found == {"repo": "u/d", "revision": "abc",
                     "path": "seconds/20260101-000000"}
    assert hub.uploaded == []


def test_rebuild_measures_them_again(tmp_path, monkeypatch, hub):
    data = _logs(tmp_path)
    inputs = {"logs": seconds.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]),
              "count": 2, "min_speed": 5.0}
    hub.files = {"seconds/20260101-000000/meta.json": {"inputs": inputs}}
    monkeypatch.setattr(seconds, "seconds_above",
                        lambda logs, min_speed: {p: 2.0 for p in logs})
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
