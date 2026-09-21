# score

`score` gives each row of a set every fitted model's score, and marks the rows a rule
hits. [calibrate](calibrate.md) runs it on the calibration set and takes the
thresholds from the scores. [run test set](run_test_set.md) runs it on a test set and
counts what the detectors catch. A new threshold or `HOLD` then needs no rescoring.

A row keeps its place in the set, scored or not, since `HOLD` counts rows in a row. A
model scores only the moving rows, z-scored on the same
[scale](../../preprocess/docs/scale.md) the models were fitted on. Every other row
gets NaN. [moving](../../preprocess/docs/moving.md) says why only moving rows are used.

It writes one directory of the runs repository, `scores/<time>/`.

## Running it

```
python3 -m evaluate.score repo revision <set> local_dir runs_repo revision models/<time> runs_dir [--rebuild] [--onnx_files <dir> --precision <precision>]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding the set |
| `revision` | commit of `repo` to read the set at |
| `<set>` | the set whose rows are scored, `calibration_sets/<time>` or `test_sets/<time>`. The log split and grid it names are read too |
| `local_dir` | local folder the dataset directories are downloaded to |
| `runs_repo` | Hugging Face model repo holding the models and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the models at, as [fit](fit.md) printed it |
| `models/<time>` | the fitted models that score the rows |
| `runs_dir` | local folder the models are downloaded to and `scores/<time>/` is written to |
| `--rebuild` | score again even if `runs_repo` already holds a directory with the same `inputs` |
| `--onnx_files <dir>` | score each model with its ONNX file in `<dir>` instead of its weights, `quantize/<time>` for int8 |
| `--precision <precision>` | which ONNX file of each model, `float` or `int8` |

With `--onnx_files` the `revision` has to hold `<dir>` too. It stops when `<dir>` is
not made from `models/<time>`.

It writes these files into `runs_dir/scores/<time>/` and uploads that directory to
`runs_repo` as `scores/<time>/`.

| file | holds |
|---|---|
| `scores.npy` | float32, one row per row of the set and one column per model, NaN where the model did not score |
| `rule_hits.npy` | bool, one per row of the set, whether an instant rule hits it on a moving row |
| `models.json` | the models of the columns in order, as [models.schema.json](../../common/schemas/models.schema.json) describes |
| `meta.json` | where the rows and the models came from, as [meta.scores.schema.json](../../common/schemas/meta.scores.schema.json) describes |
