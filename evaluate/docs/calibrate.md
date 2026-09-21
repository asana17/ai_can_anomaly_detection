# calibrate

Every model gives each row a score. A row counts as an anomaly when that score is over
the model's threshold. `calibrate` sets those thresholds.

It reads the models [fit](fit.md) uploaded. It scores the calibration rows with each
of them, in torch or with its ONNX file. It puts each model's threshold where `TARGET`
of those rows sit above it. It then uploads one threshold per model, as a directory of
the runs repository. No model is fitted here.

## Running it

```
python3 -m evaluate.calibrate runs_repo revision models/<time> runs_dir local_dir [--rebuild] [--onnx_files <dir> --precision <precision>]
```

| argument | |
|---|---|
| `runs_repo` | Hugging Face model repo holding the run and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the run at, as [fit](fit.md) printed it |
| `models/<time>` | the fitted models to give a threshold to |
| `runs_dir` | local folder the models are downloaded to and `thresholds/<time>/` is written to |
| `local_dir` | local folder the dataset directories those models name are downloaded to |
| `--rebuild` | read the thresholds again even if `runs_repo` already holds a directory with the same `inputs` |
| `--onnx_files <dir>` | score each model with its ONNX file in `<dir>` instead of its weights, `quantize/<time>` for int8 |
| `--precision <precision>` | which ONNX file of each model, `float` or `int8` |

Without `--onnx_files` each model scores in torch, on the weights [fit](fit.md) wrote
into `models/<time>`. With `--onnx_files` the `revision` has to hold `<dir>` too. It
stops when `<dir>` is not made from `models/<time>`.

An int8 file does not score a row quite as the float model does, so it cannot keep
the float model's threshold. Its threshold is taken with `--onnx_files` and
`--precision int8`.

It writes these files into `runs_dir/thresholds/<time>/` and uploads that directory to
`runs_repo` as `thresholds/<time>/`.

| file | holds |
|---|---|
| `thresholds.json` | each model's threshold, as [thresholds.schema.json](../../common/schemas/thresholds.schema.json) describes |
| `meta.json` | where the models and the rows came from, as [meta.thresholds.schema.json](../../common/schemas/meta.thresholds.schema.json) describes |

## The rows it scores

calibrate scores the calibration rows of the train set the models were fitted on. A
model has never seen them, and [train_set](../../assemble/docs/train_set.md) says why
they are held back.

Rows at or below `MIN_SPEED` are dropped, as they are in [fit](fit.md). So are rows an
instant rule already flags, since a model is only asked about the rows the rules let
through. What is left is z-scored on the same [scale](../../assemble/docs/scale.md)
the models were fitted on.

## The threshold

A model's threshold is the score that `TARGET` of those rows sit above. At `TARGET`
0.001, one calibration row in a thousand is over it, and a detector that flags rows
above it raises about that many false alarms on traffic like the calibration rows.
