# split_test_logs

`split_test_logs` cuts the logs into test and non-test logs by time. Whole logs go to
one side or the other. [attack_set](attack_set.md) attacks the test logs.
[calibration_set](calibration_set.md) and [train_set](train_set.md) take their rows
from the non-test logs.

## Example

```python
seconds = seconds_of(raw, counts, logs, min_speed=min_speed, period=period)
# the logs are cut into n_splits parts by time, and part number fold becomes test
non_test_logs, test_logs = split(seconds, n_splits, fold)
```

`raw`, `counts` and `logs` are the rows and `logs.json` of a [grid](grid.md).

## Running it

```
python3 -m assemble.split_test_logs repo revision grids/<time> local_dir [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `grids/<time>/` and uploaded to, needs `hf auth login` |
| `revision` | commit of `repo` to read `grids/<time>/` at, as [grid](grid.md) printed it |
| `grids/<time>` | the [grid](grid.md) directory whose rows are counted and cut |
| `local_dir` | local folder `log_splits/<time>/` is written to, kept after the upload |
| `--rebuild` | cut even if `repo` already has `log_splits/<time>/` for the same `grids/<time>`, `MIN_SPEED`, `N_SPLITS` and `FOLD` |

It writes these files into `local_dir/log_splits/<time>/` and uploads that directory to
`repo` as `log_splits/<time>/`.

| file | holds |
|---|---|
| `log_split.json` | `non_test` and `test`, the logs of each, and the first and last time of the test span, as [log_split.schema.json](../../common/schemas/log_split.schema.json) describes. `read_log_split` reads it back |
| `seconds.json` | each log's seconds above `MIN_SPEED`, counted off the grid, as [seconds.schema.json](../../common/schemas/seconds.schema.json) describes |
| `meta.json` | where the log split came from, as [meta.log_splits.schema.json](../../common/schemas/meta.log_splits.schema.json) describes |

## The parts are sized by the seconds above the minimum speed

Only the rows above `min_speed` are used.
[moving](../../preprocess/docs/moving.md#why-only-the-moving-rows) says why. So the
logs are cut on their seconds above `min_speed`. `seconds_of` counts each log's
[moving](../../preprocess/docs/moving.md) rows on the [grid](grid.md).
