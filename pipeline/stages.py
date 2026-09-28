"""Run every stage from the grid to the window test run, each on what the one before
made."""

from __future__ import annotations

from assemble import calibration_set, grid, split_test_logs, test_set, train_set
from common.cli import arguments
from common.hub_dirs import print_header
from common.settings import read_settings
from deploy import export, export_windows, quantize
from evaluate import run_test_set, run_window_test_set
from models import calibrate, calibrate_windows, fit, fit_windows


STAGES = (grid, split_test_logs, calibration_set, train_set, test_set, fit, export,
          quantize, calibrate, fit_windows, export_windows, calibrate_windows,
          run_test_set, run_window_test_set)


def main(data_repo, can_data_dir, can_data_pattern, local_data_dir, runs_repo,
         local_runs_dir, settings, models, window_models, dry_run=False, rebuild=()):
    """Run every stage, building the ones `rebuild` names, such as `assemble.test_set`,
    again even when one made from the same inputs is there.

    The test set and the two test runs are made once for each of `ATTACKS`, and the
    window test runs are returned in that order.
    """
    unknown = set(rebuild) - {stage.__name__ for stage in STAGES}
    if unknown:
        raise SystemExit(f"no stage is named {', '.join(sorted(unknown))}")
    again = {stage: stage.__name__ in rebuild for stage in STAGES}
    each = read_settings(settings)
    print_header()
    grids = grid.main(can_data_dir, can_data_pattern, local_data_dir, data_repo,
                      settings=each.grid, rebuild=again[grid], dry_run=dry_run)
    log_split = split_test_logs.main(data_repo, grids["revision"], grids["path"],
                                     local_data_dir, settings=each.split_test_logs,
                                     rebuild=again[split_test_logs], dry_run=dry_run)
    calibration = calibration_set.main(data_repo, log_split["revision"],
                                       log_split["path"], local_data_dir,
                                       settings=each.calibration_set,
                                       rebuild=again[calibration_set], dry_run=dry_run)
    train = train_set.main(data_repo, calibration["revision"], calibration["path"],
                           local_data_dir, settings=each.train_set,
                           rebuild=again[train_set], dry_run=dry_run)
    fitted = fit.main(data_repo, train["revision"], train["path"], local_data_dir,
                      runs_repo, local_runs_dir, models=models, rebuild=again[fit],
                      dry_run=dry_run)
    onnx = export.main(runs_repo, fitted["revision"], fitted["path"], local_runs_dir,
                       rebuild=again[export], dry_run=dry_run)
    quantize.main(runs_repo, onnx["revision"], onnx["path"], local_runs_dir,
                  local_data_dir, settings=each.quantize, rebuild=again[quantize],
                  dry_run=dry_run)
    thresholds = calibrate.main(runs_repo, fitted["revision"], fitted["path"],
                                local_runs_dir, local_data_dir, settings=each.calibrate,
                                rebuild=again[calibrate], dry_run=dry_run)
    fitted_windows = fit_windows.main(data_repo, train["revision"], train["path"],
                                      local_data_dir, runs_repo, local_runs_dir,
                                      models=window_models, rebuild=again[fit_windows],
                                      dry_run=dry_run)
    export_windows.main(runs_repo, fitted_windows["revision"], fitted_windows["path"],
                        local_runs_dir, rebuild=again[export_windows], dry_run=dry_run)
    window_thresholds = calibrate_windows.main(
        runs_repo, fitted_windows["revision"], fitted_windows["path"], local_runs_dir,
        local_data_dir, settings=each.calibrate, rebuild=again[calibrate_windows],
        dry_run=dry_run)
    window_test_runs = []
    for attack in each.test_set.ATTACKS:
        test = test_set.main(data_repo, log_split["revision"], log_split["path"],
                             can_data_dir, local_data_dir, attack=attack,
                             settings=each.test_set, rebuild=again[test_set],
                             dry_run=dry_run)
        test_run = run_test_set.main(data_repo, test["revision"], test["path"],
                                     local_data_dir, runs_repo, thresholds["revision"],
                                     thresholds["path"], local_runs_dir,
                                     settings=each.run_test_set,
                                     rebuild=again[run_test_set], dry_run=dry_run)
        window_test_runs.append(run_window_test_set.main(
            runs_repo, test_run["revision"], test_run["path"],
            window_thresholds["revision"], window_thresholds["path"], local_data_dir,
            local_runs_dir, rebuild=again[run_window_test_set], dry_run=dry_run))
    return window_test_runs


if __name__ == "__main__":
    main(**arguments(("data_repo", "can_data_dir", "can_data_pattern", "local_data_dir",
                      "runs_repo", "local_runs_dir", "settings", "models",
                      "window_models"),
                     dry_run=False, rebuild=[]))
