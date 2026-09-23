import json
import os

from common.settings import RunSettings, SplitSettings
from pipeline import stages, worktree


def test_each_stage_reads_what_the_one_before_made(monkeypatch, tmp_path):
    calls = {}

    def stage(name):
        def main(*args, **flags):
            calls[name] = (args, flags)
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

    (tmp_path / "s.json").write_text(json.dumps({"split_test_logs": {"FOLD": 0}}))
    stages.main("u/d", "data", "part_*/*.csv", "out", "u/r", "runs",
                str(tmp_path / "s.json"), "m.json")

    def s(stage):
        return {"settings": getattr(RunSettings(), stage), "dry_run": False}

    assert calls["grids"] == (("data", "part_*/*.csv", "out", "u/d"), s("grid"))
    assert calls["log_splits"] == (("u/d", "grids-rev", "grids/t", "out"), {
        "settings": SplitSettings(FOLD=0), "dry_run": False})
    assert calls["calibration_sets"] == (("u/d", "log_splits-rev", "log_splits/t",
                                          "out"), s("calibration_set"))
    assert calls["train_sets"] == (("u/d", "calibration_sets-rev", "calibration_sets/t",
                                    "out"), s("train_set"))
    assert calls["test_sets"] == (("u/d", "log_splits-rev", "log_splits/t", "data",
                                   "out"), s("test_set"))
    assert calls["models"] == (("u/d", "train_sets-rev", "train_sets/t", "out", "u/r",
                                "runs"), {"models": "m.json", "dry_run": False})
    assert calls["onnx"] == (("u/r", "models-rev", "models/t", "runs"),
                             {"dry_run": False})
    assert calls["quantize"] == (("u/r", "onnx-rev", "onnx/t", "runs", "out"),
                                 s("quantize"))
    assert calls["thresholds"] == (("u/r", "models-rev", "models/t", "runs", "out"),
                                   s("calibrate"))
    assert calls["test_runs"] == (("u/d", "test_sets-rev", "test_sets/t", "out", "u/r",
                                   "thresholds-rev", "thresholds/t", "runs"),
                                  s("run_test_set"))


def test_it_runs_the_stages_in_a_worktree_with_copies_of_the_files(monkeypatch,
                                                                   tmp_path):
    (tmp_path / "s.json").write_text(json.dumps({"split_test_logs": {"FOLD": 0}}))
    (tmp_path / "m.json").write_text("[]")
    ran = []

    def git(*args):
        os.makedirs(args[-2])
        ran.append(args)

    monkeypatch.setattr(worktree, "git", git)
    monkeypatch.setattr(worktree.subprocess, "run",
                        lambda args, **k: ran.append((args, k)))
    worktree.main(str(tmp_path / "work"), "u/d", "data", "*.csv", "out", "u/r", "runs",
                  str(tmp_path / "s.json"), str(tmp_path / "m.json"))

    (run_dir,) = (tmp_path / "work").iterdir()
    assert ran[0] == ("worktree", "add", "--detach", str(run_dir / "code"), "HEAD")
    assert json.loads((run_dir / "settings.json").read_text()) == {
        "split_test_logs": {"FOLD": 0}}
    args, flags = ran[1]
    assert args[-2:] == [str(run_dir / "settings.json"), str(run_dir / "models.json")]
    assert flags["cwd"] == str(run_dir / "code")


def test_a_dry_run_passes_it_on_and_removes_its_worktree(monkeypatch, tmp_path):
    (tmp_path / "s.json").write_text("{}")
    (tmp_path / "m.json").write_text("[]")
    ran = []

    def git(*args):
        if args[1] == "add":
            os.makedirs(args[-2])
        ran.append(args)

    monkeypatch.setattr(worktree, "git", git)
    monkeypatch.setattr(worktree.subprocess, "run", lambda args, **k: ran.append(args))
    worktree.main(str(tmp_path / "work"), "u/d", "data", "*.csv", "out", "u/r", "runs",
                  str(tmp_path / "s.json"), str(tmp_path / "m.json"), dry_run=True)

    assert ran[1][-1] == "--dry-run"
    assert ran[2][:3] == ("worktree", "remove", "--force")
    assert not (tmp_path / "work").exists()
