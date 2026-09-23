import pytest

from common.cli import arguments


def test_the_positional_names_come_back_under_their_names(monkeypatch):
    monkeypatch.setattr("sys.argv", ["stage", "u/d", "abc", "out"])
    assert arguments(("repo", "revision", "local_dir")) == {
        "repo": "u/d", "revision": "abc", "local_dir": "out"}


def test_a_false_flag_is_a_switch(monkeypatch):
    monkeypatch.setattr("sys.argv", ["stage", "out", "--rebuild"])
    assert arguments(("local_dir",), rebuild=False) == {"local_dir": "out",
                                                        "rebuild": True}
    monkeypatch.setattr("sys.argv", ["stage", "out"])
    assert arguments(("local_dir",), rebuild=False) == {"local_dir": "out",
                                                        "rebuild": False}


def test_any_other_flag_keeps_its_default(monkeypatch):
    monkeypatch.setattr("sys.argv", ["stage", "out"])
    assert arguments(("local_dir",), models="models.json") == {
        "local_dir": "out", "models": "models.json"}
    monkeypatch.setattr("sys.argv", ["stage", "out", "--models", "mine.json"])
    assert arguments(("local_dir",), models="models.json") == {
        "local_dir": "out", "models": "mine.json"}


def test_a_missing_positional_stops_the_stage(monkeypatch):
    monkeypatch.setattr("sys.argv", ["stage"])
    with pytest.raises(SystemExit):
        arguments(("local_dir",))


def test_a_flag_is_written_with_a_hyphen(monkeypatch):
    monkeypatch.setattr("sys.argv", ["stage", "out", "--dry-run", "--onnx-files", "q"])
    assert arguments(("local_dir",), dry_run=False, onnx_files=None) == {
        "local_dir": "out", "dry_run": True, "onnx_files": "q"}


def test_a_list_flag_gathers_every_time_it_is_given(monkeypatch):
    monkeypatch.setattr("sys.argv",
                        ["stage", "out", "--rebuild", "a", "--rebuild", "b"])
    assert arguments(("local_dir",), rebuild=[]) == {"local_dir": "out",
                                                     "rebuild": ["a", "b"]}
    monkeypatch.setattr("sys.argv", ["stage", "out"])
    assert arguments(("local_dir",), rebuild=[]) == {"local_dir": "out", "rebuild": []}
