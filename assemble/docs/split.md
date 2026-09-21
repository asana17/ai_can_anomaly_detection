# split

`split` cuts the logs into train and test. The training rows are cut into train and
calibration rows by [train_set](train_set.md).

## Example

```python
seconds = seconds_of(raw, counts, logs, min_speed=min_speed, period=period)
# the logs are cut into n_splits blocks by time, and block number fold becomes test
train_logs, test_logs = split(seconds, n_splits, fold)
```

`raw`, `counts` and `logs` are the rows and `logs.json` of a [grid](grid.md).

## Running it

```
python3 -m assemble.split repo revision grids/<time> local_dir [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `grids/<time>/` and uploaded to, needs `hf auth login` |
| `revision` | commit of `repo` to read `grids/<time>/` at, as [grid](grid.md) printed it |
| `grids/<time>` | the [grid](grid.md) directory whose rows are counted and cut |
| `local_dir` | local folder `splits/<time>/` is written to, kept after the upload |
| `--rebuild` | cut even if `repo` already has `splits/<time>/` for the same `grids/<time>`, `MIN_SPEED`, `N_SPLITS` and `FOLD` |

It writes these files into `local_dir/splits/<time>/` and uploads that directory to
`repo` as `splits/<time>/`.

| file | holds |
|---|---|
| `split.json` | `train` and `test`, the logs of each, and the first and last time of the test block, as [split.schema.json](../../common/schemas/split.schema.json) describes. `read_split` reads it back |
| `seconds.json` | each log's seconds above `MIN_SPEED`, counted off the grid, as [seconds.schema.json](../../common/schemas/seconds.schema.json) describes |
| `meta.json` | where the split came from, as [meta.splits.schema.json](../../common/schemas/meta.splits.schema.json) describes |

## Train and test are sized by the seconds above the minimum speed

Only rows above `min_speed` are scored, and only they set the threshold. Everything
slower is left to the rules.

The truck is parked for long runs of consecutive logs, so a part chosen by log count
alone can hold no scoreable row at all.

So the cut is made on the seconds above `min_speed`. `seconds_of` counts each log's
moving rows on the [grid](grid.md), giving 0 for a log the truck sat still through and
the log's whole length for one it drove right through.

