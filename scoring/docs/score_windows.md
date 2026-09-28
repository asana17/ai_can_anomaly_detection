# score_windows

`score_windows` scores the windows of a calibration set or a test set with every
window model. It writes `window_scores/<time>/` in the runs repository. The rule hits
and the row scores of the same set come from [score](score.md).

## Running it

```
python3 -m scoring.score_windows repo revision <set> local_dir runs_repo revision window_models/<time> runs_dir [--rebuild] [--onnx-files window_onnx/<time>]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding the set |
| `revision` | commit of `repo` to read the set at |
| `<set>` | `calibration_sets/<time>` or `test_sets/<time>` |
| `local_dir` | local folder the set is downloaded to |
| `runs_repo` | Hugging Face model repo holding the window models. The scores are uploaded to it |
| `revision` | commit of `runs_repo` to read the window models at |
| `window_models/<time>` | the window models, from [fit_windows](../../models/docs/fit_windows.md) |
| `runs_dir` | local folder the window models are downloaded to and the scores are written to |
| `--rebuild` | score again even if `runs_repo` already has the same scores |
| `--onnx-files window_onnx/<time>` | score with the float ONNX files of that window export instead of the weights, or with the int8 files of its `window_quantize/<time>` |

With `--onnx-files` the `revision` has to hold `window_onnx/<time>` too. It stops when
the export is not made from `window_models/<time>`. The columns are the models the
export holds. A vector autoregression is not exported, so it gets no column.

| file | holds |
|---|---|
| `scores.npy` | float32, one row per row of the set, one column per model |
| `models.json` | the model of each column |
| `meta.json` | as [meta.window_scores.schema.json](../../common/schemas/meta.window_scores.schema.json) describes |

`scores.npy` has the same rows, in the same order, as the files [score](score.md)
writes for the same set. So row `i` of the window scores, of the row scores and of
the rule hits is the same grid row. For a calibration set, these are the calibration
rows only, which are all moving. For a test set, they are every row of the test logs,
moving or stopped.

## The windows

A window is `rows` consecutive moving rows in one segment, oldest first. `rows` is the
model's own value in `models.json`.

The set gives each row a segment id. The calibration rows come from separate blocks,
so two neighbouring calibration rows can be far apart in time. Their segment ids
differ there, so no window joins them.

The rows are z-scored on the scale of the fit before the cut. The models run in
torch, or in ONNX Runtime with `--onnx-files`. A window goes into the ONNX file as one
row of `rows` × signals values, and scores by the error on its last row, as in torch.

The windows are cut and scored `WINDOWS` at a time, a constant in `score_windows.py`,
so the memory scoring takes does not grow with the calibration set or test set.

```python
position = positions(moving(rows_of_set), segments)
ends = window_ends(position, rows=model.rows)
windows = window_rows(scaled_rows_of_set, ends, rows=model.rows)
```

Each window gets one score. It is written to `scores.npy` at the window's newest row.
The other rows have NaN. These are stopped rows, and the first `rows - 1` rows after a
stop or a segment change.

Windows are cut with `stride` 1, so every possible window has a score. Windows cut
with a larger `stride` are a subset of them. Their scores can be picked out of
`scores.npy` without scoring again.
