# pipeline

Runs every stage from [assemble.grid](../assemble/docs/grid.md) to
[evaluate.run_test_set](../evaluate/docs/run_test_set.md) in one command. It takes
hours and uploads to both Hugging Face repos, so run it only when asked to.

A stage whose inputs the repo already holds is not run again, its directory is passed
on.

## Running it

1. Write the run's values into two files outside the repository. Leave the code as it is.
   - `SETTINGS`, an object for each stage whose [settings](../common/settings.py)
     differ from the defaults, such as `{"split_test_logs": {"FOLD": 0}}`. `{}` keeps
     every default.
   - `MODELS`, the models to fit with their seeds, in the form of
     [models.json](../models/models.json).
2. Check what will run. Each stage prints one line, the date of the one it would use,
   or `<new>` when this run would build it, with the values it would be made with.
   This makes nothing.

   ```
   python3 -m pipeline.worktree WORK_DIR REPO DATA_DIR PATTERN LOCAL_DIR RUNS_REPO RUNS_DIR SETTINGS MODELS --dry-run
   ```

3. Run it in the background.

   ```
   nohup caffeinate -i python3 -m pipeline.worktree WORK_DIR REPO DATA_DIR PATTERN LOCAL_DIR RUNS_REPO RUNS_DIR SETTINGS MODELS > LOG 2>&1 &
   ```

The code that runs is HEAD's, not this tree's. Commit a change before the run that
should use it. Editing anything once it runs changes nothing.

| argument | |
|---|---|
| `WORK_DIR` | a folder outside this repository. The run gets `WORK_DIR/<time>/`, HEAD is checked out into its `code/` and the two files are copied next to it |
| `REPO` | Hugging Face dataset repo, as [grid](../assemble/docs/grid.md) takes it |
| `DATA_DIR` | local folder holding the CAN frame logs |
| `PATTERN` | glob of the logs, quoted, e.g. `"part_*/*.csv"` |
| `LOCAL_DIR` | local folder the dataset directories are written to |
| `RUNS_REPO` | Hugging Face model repo, as [fit](../models/docs/fit.md) takes it |
| `RUNS_DIR` | local folder the runs directories are written to |
| `SETTINGS` | JSON file of each stage's values that differ from the defaults |
| `MODELS` | JSON file of the models to fit |
| `--dry-run` | check what will run in a temporary worktree, removed after |

`LOG` starts with the run's folder and ends with the `test_runs/<time>` it wrote. When
it is done, remove the worktree with `git worktree remove WORK_DIR/<time>/code`.
