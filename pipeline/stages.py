"""Run every stage from the grid to the test run, each on what the one before made."""

from __future__ import annotations

from assemble import calibration_set, grid, split_test_logs, test_set, train_set
from common.cli import arguments
from evaluate import run_test_set
from models import calibrate, fit


def main(repo, data_dir, pattern, local_dir, runs_repo, runs_dir, settings, models):
    grids = grid.main(data_dir, pattern, local_dir, repo, settings=settings)
    log_split = split_test_logs.main(repo, grids["revision"], grids["path"], local_dir,
                                     settings=settings)
    calibration = calibration_set.main(repo, log_split["revision"], log_split["path"],
                                       local_dir, settings=settings)
    train = train_set.main(repo, calibration["revision"], calibration["path"],
                           local_dir, settings=settings)
    test = test_set.main(repo, log_split["revision"], log_split["path"], data_dir,
                         local_dir, settings=settings)
    fitted = fit.main(repo, train["revision"], train["path"], local_dir, runs_repo,
                      runs_dir, models=models)
    thresholds = calibrate.main(runs_repo, fitted["revision"], fitted["path"], runs_dir,
                                local_dir, settings=settings)
    return run_test_set.main(repo, test["revision"], test["path"], local_dir, runs_repo,
                             thresholds["revision"], thresholds["path"], runs_dir,
                             settings=settings)


if __name__ == "__main__":
    main(**arguments(("repo", "data_dir", "pattern", "local_dir", "runs_repo",
                      "runs_dir", "settings", "models")))
