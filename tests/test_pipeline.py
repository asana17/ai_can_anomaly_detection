import json
import os

import pytest

from common.settings import RunSettings, SplitSettings
from pipeline import stages, worktree


@pytest.fixture
def calls(monkeypatch):
    """What each stage was called with, every stage stood in for."""
    called = {}

    def stage(name):
        def main(*args, **flags):
            called[name] = (args, flags)
            return {"repo": "r", "revision": f"{name}-rev", "path": f"{name}/t"}
        return main

    for module, name in ((stages.grid, "grids"), (stages.split_test_logs, "log_splits"),
                         (stages.calibration_set, "calibration_sets"),
                         (stages.train_set, "train_sets"),
                         (stages.test_set, "test_sets"),
                         (stages.fit, "models"), (stages.export, "onnx"),
                         (stages.quantize, "quantize"),
                         (stages.calibrate, "thresholds"),
                         (stages.run_test_set, "test_runs")):
        monkeypatch.setattr(module, "main", stage(name))
    return called


def test_each_stage_reads_what_the_one_before_made(calls, tmp_path):
    (tmp_path / "s.json").write_text(json.dumps({"split_test_logs": {"FOLD": 0}}))
    stages.main("u/d", "data", "part_*/*.csv", "out", "u/r", "runs",
                str(tmp_path / "s.json"), "m.json")

    def s(stage):
        return {"settings": getattr(RunSettings(), stage), "rebuild": False,
                "dry_run": False}

    assert calls["grids"] == (("data", "part_*/*.csv", "out", "u/d"), s("grid"))
    assert calls["log_splits"] == (("u/d", "grids-rev", "grids/t", "out"), {
        "settings": SplitSettings(FOLD=0), "rebuild": False, "dry_run": False})
    assert calls["calibration_sets"] == (("u/d", "log_splits-rev", "log_splits/t",
                                          "out"), s("calibration_set"))
    assert calls["train_sets"] == (("u/d", "calibration_sets-rev", "calibration_sets/t",
                                    "out"), s("train_set"))
    assert calls["test_sets"] == (("u/d", "log_splits-rev", "log_splits/t", "data",
                                   "out"), s("test_set"))
    assert calls["models"] == (("u/d", "train_sets-rev", "train_sets/t", "out", "u/r",
                                "runs"),
                               {"models": "m.json", "rebuild": False, "dry_run": False})
    assert calls["onnx"] == (("u/r", "models-rev", "models/t", "runs"),
                             {"rebuild": False, "dry_run": False})
    assert calls["quantize"] == (("u/r", "onnx-rev", "onnx/t", "runs", "out"),
                                 s("quantize"))
    assert calls["thresholds"] == (("u/r", "models-rev", "models/t", "runs", "out"),
                                   s("calibrate"))
    assert calls["test_runs"] == (("u/d", "test_sets-rev", "test_sets/t", "out", "u/r",
                                   "thresholds-rev", "thresholds/t", "runs"),
                                  s("run_test_set"))


def test_rebuild_builds_the_stages_it_names_alone(calls, tmp_path):
    (tmp_path / "s.json").write_text("{}")
    stages.main("u/d", "data", "*.csv", "out", "u/r", "runs", str(tmp_path / "s.json"),
                "m.json", rebuild=["assemble.test_set", "models.fit"])
    assert [name for name, (_, flags) in calls.items() if flags["rebuild"]] == [
        "test_sets", "models"]


def test_rebuild_of_a_stage_there_is_not_stops_it(calls, tmp_path):
    (tmp_path / "s.json").write_text("{}")
    with pytest.raises(SystemExit):
        stages.main("u/d", "data", "*.csv", "out", "u/r", "runs",
                    str(tmp_path / "s.json"), "m.json", rebuild=["assemble.test"])
    assert calls == {}


def test_it_runs_the_stages_in_a_worktree_with_copies_of_the_files(monkeypatch,
                                                                   tmp_path):
    written = {"pipeline": {"snapshot_dir": str(tmp_path / "work")},
               "split_test_logs": {"FOLD": 0}}
    (tmp_path / "s.json").write_text(json.dumps(written))
    (tmp_path / "m.json").write_text("[]")
    ran = []

    def git(*args):
        os.makedirs(args[-2])
        ran.append(args)

    monkeypatch.setattr(worktree, "git", git)
    monkeypatch.setattr(worktree.subprocess, "run",
                        lambda args, **k: ran.append((args, k)))
    worktree.main(str(tmp_path / "s.json"), str(tmp_path / "m.json"))

    (run_dir,) = (tmp_path / "work").iterdir()
    assert ran[0] == ("worktree", "add", "--detach", str(run_dir / "code"), "HEAD")
    assert json.loads((run_dir / "settings.json").read_text()) == written
    args, flags = ran[1]
    assert args[3:6] == ["asana17/ai_can_anomaly_detection_data",
                         os.path.abspath("data"), "part_*/*.csv"]
    assert args[-2:] == [str(run_dir / "settings.json"), str(run_dir / "models.json")]
    assert flags["cwd"] == str(run_dir / "code")


def test_a_dry_run_passes_it_on_and_removes_its_worktree(monkeypatch, tmp_path):
    (tmp_path / "s.json").write_text(json.dumps(
        {"pipeline": {"snapshot_dir": str(tmp_path / "work")}}))
    (tmp_path / "m.json").write_text("[]")
    ran = []

    def git(*args):
        if args[1] == "add":
            os.makedirs(args[-2])
        ran.append(args)

    monkeypatch.setattr(worktree, "git", git)
    monkeypatch.setattr(worktree.subprocess, "run", lambda args, **k: ran.append(args))
    worktree.main(str(tmp_path / "s.json"), str(tmp_path / "m.json"), dry_run=True)

    assert ran[1][-1] == "--dry-run"
    assert ran[2][:3] == ("worktree", "remove", "--force")
    assert not (tmp_path / "work").exists()


def test_rebuild_is_passed_on_to_the_stages(monkeypatch, tmp_path):
    (tmp_path / "s.json").write_text(json.dumps(
        {"pipeline": {"snapshot_dir": str(tmp_path / "work")}}))
    (tmp_path / "m.json").write_text("[]")
    ran = []
    monkeypatch.setattr(worktree, "git", lambda *args: os.makedirs(args[-2]))
    monkeypatch.setattr(worktree.subprocess, "run", lambda args, **k: ran.append(args))
    worktree.main(str(tmp_path / "s.json"), str(tmp_path / "m.json"),
                  rebuild=["assemble.test_set", "models.fit"])
    assert ran[0][-4:] == ["--rebuild", "assemble.test_set", "--rebuild", "models.fit"]
