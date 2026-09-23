"""Run every stage from the grid to the test run, each on what the one before made."""

from __future__ import annotations

from assemble import calibration_set, grid, split_test_logs, test_set, train_set
from common.cli import arguments
from common.hub_dirs import print_header
from common.settings import read_settings
from deploy import export, quantize
from evaluate import run_test_set
from models import calibrate, fit


def main(repo, data_dir, pattern, local_dir, runs_repo, runs_dir, settings, models,
         dry_run=False):
    each = read_settings(settings)
    print_header()
    grids = grid.main(data_dir, pattern, local_dir, repo, settings=each.grid,
                      dry_run=dry_run)
    log_split = split_test_logs.main(repo, grids["revision"], grids["path"], local_dir,
                                     settings=each.split_test_logs, dry_run=dry_run)
    calibration = calibration_set.main(repo, log_split["revision"], log_split["path"],
                                       local_dir, settings=each.calibration_set,
                                       dry_run=dry_run)
    train = train_set.main(repo, calibration["revision"], calibration["path"],
                           local_dir, settings=each.train_set, dry_run=dry_run)
    test = test_set.main(repo, log_split["revision"], log_split["path"], data_dir,
                         local_dir, settings=each.test_set, dry_run=dry_run)
    fitted = fit.main(repo, train["revision"], train["path"], local_dir, runs_repo,
                      runs_dir, models=models, dry_run=dry_run)
    onnx = export.main(runs_repo, fitted["revision"], fitted["path"], runs_dir,
                       dry_run=dry_run)
    quantize.main(runs_repo, onnx["revision"], onnx["path"], runs_dir, local_dir,
                  settings=each.quantize, dry_run=dry_run)
    thresholds = calibrate.main(runs_repo, fitted["revision"], fitted["path"], runs_dir,
                                local_dir, settings=each.calibrate, dry_run=dry_run)
    return run_test_set.main(repo, test["revision"], test["path"], local_dir, runs_repo,
                             thresholds["revision"], thresholds["path"], runs_dir,
                             settings=each.run_test_set, dry_run=dry_run)


if __name__ == "__main__":
    main(**arguments(("repo", "data_dir", "pattern", "local_dir", "runs_repo",
                      "runs_dir", "settings", "models"), dry_run=False))
