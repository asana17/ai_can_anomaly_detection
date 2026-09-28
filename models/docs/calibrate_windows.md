# calibrate_windows

`calibrate_windows` gives every window model a threshold. A window counts as an
anomaly when its score is over the threshold of its model. It writes
`window_thresholds/<time>/` in the runs repository. No model is fitted here.

## Running it

```
python3 -m models.calibrate_windows runs_repo revision window_models/<time> runs_dir local_dir [--rebuild] [--onnx-files window_onnx/<time>]
```

| argument | |
|---|---|
| `runs_repo` | Hugging Face model repo holding the window models. The thresholds are uploaded to it |
| `revision` | commit of `runs_repo` to read the window models at |
| `window_models/<time>` | the window models, from [fit_windows](fit_windows.md) |
| `runs_dir` | local folder the window models are downloaded to and the scores and thresholds are written to |
| `local_dir` | local folder the calibration set is downloaded to |
| `--rebuild` | take the thresholds again even if `runs_repo` already has them. The calibration set's windows are scored again too |
| `--onnx-files window_onnx/<time>` | take the thresholds from the scores of that window export's float ONNX files, as [score_windows](../../scoring/docs/score_windows.md) gives them |

| file | holds |
|---|---|
| `thresholds.json` | each model's threshold, in the same form as [calibrate](calibrate.md) writes |
| `meta.json` | as [meta.window_thresholds.schema.json](../../common/schemas/meta.window_thresholds.schema.json) describes |

## The threshold

It scores the windows of the calibration set with
[score_windows](../../scoring/docs/score_windows.md), or reuses the scores already in
the runs repository. The calibration rows were held out of the train
set the window models were fitted on, so the models have not seen them.

A model's threshold is the lowest score at which its alarm rises no more than
`WINDOW_TARGET` times an hour on the calibration set, 0.5. The alarm is the one
[run_window_test_set](../../evaluate/docs/run_window_test_set.md) counts, on while one
of the last N rows, `TestRunSettings.N`, is flagged. Flags within N rows of each other
make one alarm, and a new segment starts a new one. The hours are the moving rows of
the calibration set at 0.1 s each.

A window model is held to a number of alarms rather than a share of windows. A window
that sees an attack sees it only while the window holds it, so few of its windows are
flagged, and k of the last N would seldom be reached.

Each model takes its threshold from its own windows. So models with different `rows`
take their thresholds from different windows.

`meta.json` records how many windows each threshold was taken from.
