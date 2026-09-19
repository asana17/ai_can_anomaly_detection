import json

from common import hf_upload, hub_dirs
from assemble import seconds


class Hub:
    """Stands in for HfApi, logged in, with the directories in `metas` in the repository."""

    metas = {}
    uploaded = []

    def whoami(self):
        return {"name": "test"}

    def repo_info(self, repo, repo_type="model"):
        return type("Info", (), {"sha": "abc"})

    def list_repo_files(self, repo, repo_type="model", revision=None):
        return [f"{path}/meta.json" for path in self.metas]

    def upload_folder(self, **kwargs):
        self.uploaded.append(kwargs)
        return type("Commit", (), {"oid": "def"})


def _hub(monkeypatch, tmp_path, metas):
    Hub.metas, Hub.uploaded = metas, []
    monkeypatch.setattr(hub_dirs, "HfApi", Hub)
    monkeypatch.setattr(hf_upload, "HfApi", Hub)

    def download(repo, name, repo_type, revision, local_dir):
        path = tmp_path / "hub" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(metas[name.rsplit("/", 1)[0]]))
        return str(path)

    monkeypatch.setattr(hub_dirs, "hf_hub_download", download)


def _logs(tmp_path):
    data = tmp_path / "data" / "part_1"
    data.mkdir(parents=True)
    for name in ("a.csv", "b.csv"):
        (data / name).write_text("")
    return str(tmp_path / "data")


def test_it_measures_the_logs_named_under_data_dir(tmp_path, monkeypatch):
    _hub(monkeypatch, tmp_path, {})
    monkeypatch.setattr(seconds, "seconds_above",
                        lambda logs, min_speed: {p: 1.0 for p in logs})
    made = seconds.main(_logs(tmp_path), "part_*/*.csv", str(tmp_path / "local"), "u/d")
    folder = tmp_path / "local" / made["path"]
    assert json.loads((folder / "seconds.json").read_text()) == {
        "part_1/a.csv": 1.0, "part_1/b.csv": 1.0}
    assert made["revision"] == "def" and Hub.uploaded[0]["repo_type"] == "dataset"


def test_it_names_the_directory_built_from_the_same_logs(tmp_path, monkeypatch):
    data = _logs(tmp_path)
    inputs = {"logs": seconds.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]),
              "count": 2, "min_speed": 5.0}
    _hub(monkeypatch, tmp_path, {"seconds/20260101-000000": {"inputs": inputs}})
    monkeypatch.setattr(seconds, "seconds_above", None)     # measuring would fail
    found = seconds.main(data, "part_*/*.csv", str(tmp_path / "local"), "u/d")
    assert found == {"repo": "u/d", "revision": "abc",
                     "path": "seconds/20260101-000000"}
    assert Hub.uploaded == []


def test_rebuild_measures_them_again(tmp_path, monkeypatch):
    data = _logs(tmp_path)
    inputs = {"logs": seconds.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]),
              "count": 2, "min_speed": 5.0}
    _hub(monkeypatch, tmp_path, {"seconds/20260101-000000": {"inputs": inputs}})
    monkeypatch.setattr(seconds, "seconds_above",
                        lambda logs, min_speed: {p: 2.0 for p in logs})
    made = seconds.main(data, "part_*/*.csv", str(tmp_path / "local"), "u/d",
                        rebuild=True)
    assert made["path"] != "seconds/20260101-000000" and len(Hub.uploaded) == 1


def test_find_matches_a_tuple_to_the_list_meta_json_holds(tmp_path, monkeypatch):
    _hub(monkeypatch, tmp_path, {"splits/20260101-000000": {"inputs": {"hold": [1, 10]}}})
    found = hub_dirs.find("u/d", "splits", {"hold": (1, 10)}, str(tmp_path / "local"))
    assert found["path"] == "splits/20260101-000000"


def test_the_digest_changes_with_a_log_s_size(tmp_path):
    data = _logs(tmp_path)
    before = seconds.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"])
    (tmp_path / "data" / "part_1" / "a.csv").write_text("1")
    assert seconds.logs_digest(data, ["part_1/a.csv", "part_1/b.csv"]) != before
