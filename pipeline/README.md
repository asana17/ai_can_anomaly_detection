# pipeline

Runs every stage from [assemble.grid](../assemble/docs/grid.md) to
[evaluate.run_window_test_set](../evaluate/docs/run_window_test_set.md) in one command. It takes
hours and uploads to both Hugging Face repos, so run it only when asked to.

The window models are fitted by [fit_windows](../models/docs/fit_windows.md), exported
by [export_windows](../deploy/docs/export_windows.md) and given thresholds by
[calibrate_windows](../models/docs/calibrate_windows.md). They use the
same train set and calibration set as the row models.

A stage whose inputs the repo already holds is not run again, its directory is passed
on.

## Running it

1. Write the run's values into three files outside the repository. Leave the code as it is.
   - `SETTINGS`, an object for each stage whose [settings](../common/settings.py)
     differ from the defaults, such as `{"split_test_logs": {"FOLD": 0}}`. `{}` keeps
     every default. The folders and repos are under `pipeline`, such as
     `{"pipeline": {"local_runs_dir": "/tmp/runs"}}`. By default every folder is in
     this repository, the ignored `data/` and `out/`.
   - `MODELS`, the models to fit with their seeds, in the form of
     [models.json](../models/models.json).
   - `WINDOW_MODELS`, the window models to fit, in the form of
     [window_models.json](../models/window_models.json).
2. Check what will run. Each stage prints one line, the date of the one it would use,
   or `<new>` when this run would build it, with the values it would be made with.
   This makes nothing.

   ```
   python3 -m pipeline.worktree SETTINGS MODELS WINDOW_MODELS --dry-run
   ```

3. Run it in the background.

   ```
   nohup caffeinate -i python3 -m pipeline.worktree SETTINGS MODELS WINDOW_MODELS > LOG 2>&1 &
   ```

The code that runs is HEAD's, not this tree's. Commit a change before the run that
should use it. Editing anything once it runs changes nothing.

| argument | |
|---|---|
| `SETTINGS` | JSON file of each stage's values that differ from the defaults |
| `MODELS` | JSON file of the models to fit |
| `WINDOW_MODELS` | JSON file of the window models to fit |
| `--dry-run` | check what will run in a temporary worktree, removed after |
| `--rebuild STAGE` | build the stage named as `python3 -m` names it, such as `assemble.test_set`, even when one made from the same inputs is there. The stages after it build too. Give it again for each stage to build |

`LOG` starts with the run's folder. When it is done, remove the worktree with
`git worktree remove <snapshot_dir>/<time>/code`.
