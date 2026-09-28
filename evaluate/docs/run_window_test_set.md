# run window test set

`run_window_test_set` counts what each window model adds to the alarm on every tick, on
the attacked test rows. The alarm on every tick is the one
[run_test_set](run_test_set.md) counts, the rules and one instant model, k of the last
`n` rows. The window model is added to it with OR, as the board shows the two alarms
side by side.

The instant scores, the rule hits, the thresholds and the test set come from a
directory `run_test_set` wrote, so the alarm on every tick is the one it counted. The
window models and their thresholds come from a directory
[calibrate_windows](../../models/docs/calibrate_windows.md) wrote. It scores the test
set's windows with those models by running
[score_windows](../../scoring/docs/score_windows.md), or reuses the scores the runs
repository holds for them already. When the thresholds came from the ONNX files of a
window export, the test set's windows are scored with the same files.

It writes one directory of the runs repository, `window_test_runs/<time>/`.

## Running it

```
python3 -m evaluate.run_window_test_set runs_repo revision test_runs/<time> revision window_thresholds/<time> local_dir runs_dir [--rebuild]
```

| argument | |
|---|---|
| `runs_repo` | Hugging Face model repo holding both directories and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the test run at, as [run_test_set](run_test_set.md) printed it |
| `test_runs/<time>` | the test run whose alarm on every tick the window models are added to |
| `revision` | commit of `runs_repo` to read the window thresholds at, as [calibrate_windows](../../models/docs/calibrate_windows.md) printed it |
| `window_thresholds/<time>` | the thresholds the window models run at. The models they name are read too, and scored with |
| `local_dir` | local folder the dataset directories are downloaded to |
| `runs_dir` | local folder `window_scores/<time>/` and `window_test_runs/<time>/` are written to, kept after the upload |
| `--rebuild` | count again even if `runs_repo` already holds a directory with the same `inputs`. The test set's windows are scored again too. The instant scores are still the test run's |

It writes these files into `runs_dir/window_test_runs/<time>/` and uploads that
directory to `runs_repo` as `window_test_runs/<time>/`.

| file | holds |
|---|---|
| `window_detection.json` | one entry per instant model and window model, what they caught together at each k, as [window_detection.schema.json](../../common/schemas/window_detection.schema.json) describes |
| `meta.json` | where the scores, the thresholds and the rows came from, as [meta.window_test_runs.schema.json](../../common/schemas/meta.window_test_runs.schema.json) describes |

## A window on every row

A window model looks at the last W rows at once. Here it is scored on every row, once
W moving rows in a row have come in. Each window is the one before it moved on by one
row.

## When the window model alarms

Each window's score is saved at its last row.

The window model flags that row when the score is above its threshold. A row where no
window ends is not flagged.

The window model alarms when k of the last N rows are flagged, with the same k and N
as the alarm on every tick. The count starts again when the segment changes, as it
does for the rows.

The rules and the instant model catch an attack when they alarm on a row of the
attack. The window model's alarm catches it on a row up to W - 1 rows after the
attack's last row too, as the window ending there still holds a row of the attack.
Such an alarm is not a false positive.

## What is compared

`run_test_set` counts the alarm of the rules and the instant model. This test run
counts the same alarm with the window model added. Compare the two at each k. The
alarm is on when k of the last N rows are flagged.
