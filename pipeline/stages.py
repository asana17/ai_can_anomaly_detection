"""Run every stage from the grid to the test run, each on what the one before made."""

from __future__ import annotations

from assemble import calibration_set, grid, split_test_logs, test_set, train_set
from common.cli import arguments
from common.hub_dirs import print_header
from common.settings import read_settings
from deploy import export, quantize
from evaluate import run_test_set
from models import calibrate, fit


STAGES = (grid, split_test_logs, calibration_set, train_set, test_set, fit, export,
          quantize, calibrate, run_test_set)


def main(repo, data_dir, pattern, local_dir, runs_repo, runs_dir, settings, models,
         dry_run=False, rebuild=()):
    """Run every stage, building the ones `rebuild` names, such as `assemble.test_set`,
    again even when one made from the same inputs is there."""
    unknown = set(rebuild) - {stage.__name__ for stage in STAGES}
    if unknown:
        raise SystemExit(f"no stage is named {', '.join(sorted(unknown))}")
    again = {stage: stage.__name__ in rebuild for stage in STAGES}
    each = read_settings(settings)
    print_header()
    grids = grid.main(data_dir, pattern, local_dir, repo, settings=each.grid,
                      rebuild=again[grid], dry_run=dry_run)
    log_split = split_test_logs.main(repo, grids["revision"], grids["path"], local_dir,
                                     settings=each.split_test_logs,
                                     rebuild=again[split_test_logs], dry_run=dry_run)
    calibration = calibration_set.main(repo, log_split["revision"], log_split["path"],
                                       local_dir, settings=each.calibration_set,
                                       rebuild=again[calibration_set], dry_run=dry_run)
    train = train_set.main(repo, calibration["revision"], calibration["path"],
                           local_dir, settings=each.train_set, rebuild=again[train_set],
                           dry_run=dry_run)
    test = test_set.main(repo, log_split["revision"], log_split["path"], data_dir,
                         local_dir, settings=each.test_set, rebuild=again[test_set],
                         dry_run=dry_run)
    fitted = fit.main(repo, train["revision"], train["path"], local_dir, runs_repo,
                      runs_dir, models=models, rebuild=again[fit], dry_run=dry_run)
    onnx = export.main(runs_repo, fitted["revision"], fitted["path"], runs_dir,
                       rebuild=again[export], dry_run=dry_run)
    quantize.main(runs_repo, onnx["revision"], onnx["path"], runs_dir, local_dir,
                  settings=each.quantize, rebuild=again[quantize], dry_run=dry_run)
    thresholds = calibrate.main(runs_repo, fitted["revision"], fitted["path"], runs_dir,
                                local_dir, settings=each.calibrate,
                                rebuild=again[calibrate], dry_run=dry_run)
    return run_test_set.main(repo, test["revision"], test["path"], local_dir, runs_repo,
                             thresholds["revision"], thresholds["path"], runs_dir,
                             settings=each.run_test_set, rebuild=again[run_test_set],
                             dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("repo", "data_dir", "pattern", "local_dir", "runs_repo",
                      "runs_dir", "settings", "models"), dry_run=False, rebuild=[]))
