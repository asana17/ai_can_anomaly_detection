# calibrate

Every model gives each row a score. A row counts as an anomaly when that score is over
the model's threshold. `calibrate` sets those thresholds.

It runs [score](../../scoring/docs/score.md) on the calibration set the models'
train set names, or reuses the scores the runs repository already holds for it. It puts each model's
threshold as low as the alarm on every tick allows on those rows at `ROW_TARGET`
false alarms an hour. It then uploads one threshold
per model, as a directory of the runs repository. No model is fitted here.

## Running it

```
python3 -m models.calibrate runs_repo revision models/<time> runs_dir local_dir [--rebuild] [--onnx-files <dir> --precision <precision>]
```

| argument | |
|---|---|
| `runs_repo` | Hugging Face model repo holding the run and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the run at, as [fit](fit.md) printed it |
| `models/<time>` | the fitted models to give a threshold to |
| `runs_dir` | local folder the models are downloaded to and `scores/<time>/` and `thresholds/<time>/` are written to |
| `local_dir` | local folder the dataset directories those models name are downloaded to |
| `--rebuild` | take the thresholds again even if `runs_repo` already holds a directory with the same `inputs`. The calibration set is scored again too |
| `--onnx-files <dir>` | score each model with its ONNX file in `<dir>` instead of its weights, `quantize/<time>` for int8 |
| `--precision <precision>` | which ONNX file of each model, `float` or `int8` |

With `--onnx-files` the `revision` has to hold `<dir>` too. It stops when `<dir>` is
not made from `models/<time>`.

An int8 file does not score a row quite as the float model does, so it cannot keep
the float model's threshold. Its threshold is taken with `--onnx-files` and
`--precision int8`.

It writes these files into `runs_dir/thresholds/<time>/` and uploads that directory to
`runs_repo` as `thresholds/<time>/`.

| file | holds |
|---|---|
| `thresholds.json` | each model's threshold, as [thresholds.schema.json](../../common/schemas/thresholds.schema.json) describes |
| `meta.json` | where the models and the rows came from, as [meta.thresholds.schema.json](../../common/schemas/meta.thresholds.schema.json) describes |

## The rows the thresholds come from

calibrate takes the thresholds from the rows of the
[calibration set](../../assemble/docs/calibration_set.md) the models' train set names.
A model has never seen them, and the calibration set says why they are held back.
Every moving row counts.

## The threshold

A model's threshold is the lowest of its scores at which the alarm on every tick rises
no more than `ROW_TARGET` times an hour on the calibration rows, 1.5. The alarm is the
one [run_test_set](../../evaluate/docs/run_test_set.md) counts, on where the model or a
rule flags `ROW_K` of the last N rows, 10 of `TestRunSettings.N` 10. Rises within one
stretch of alarm count once, and a new segment starts a new one. The hours are the
moving calibration rows at 0.1 s each.

The rules raise some of those alarms on their own, and they count against the target.
When the rules alone raise more, the threshold is the model's highest score, and the
model flags nothing.

The alarm is held to its target at `ROW_K`, and counted by run_test_set at every k. At
a k below `ROW_K` it raises more.
