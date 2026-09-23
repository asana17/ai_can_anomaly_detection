# calibration_set

`calibration_set` cuts the time of the non-test logs into calibration blocks, and picks
the rows a threshold is taken from.

- A calibration row is from a non-test log and inside a calibration block.
- It is above `min_speed`.
- It is more than `gap` seconds from the test span.
- It may be one a rule hits.

It writes the blocks and which rows those are. The rows stay in the [grid](grid.md).
[train_set](train_set.md) keeps its rows away from the blocks.

The rows that set a threshold must be ones the model never saw. A model with enough
capacity fits its own training rows, so residuals on those come out smaller than on rows
it has not seen, and a threshold read off them would sit too low.

## Running it

```
python3 -m assemble.calibration_set repo revision log_splits/<time> local_dir [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `log_splits/<time>/` and uploaded to, needs `hf auth login` |
| `revision` | commit of `repo` to read `log_splits/<time>/` at, as [split_test_logs](split_test_logs.md) printed it |
| `log_splits/<time>` | the log split whose non-test logs are cut. The grid it names is read too |
| `local_dir` | local folder `calibration_sets/<time>/` is written to, kept after the upload |
| `--rebuild` | build even if `repo` already has `calibration_sets/<time>/` for the same log split, `CALIBRATION`, `BLOCK` and `GAP` |

`MIN_SPEED` comes from the log split's `meta.json` and `PERIOD` from the grid's.

It writes these files into `local_dir/calibration_sets/<time>/` and uploads that
directory to `repo` as `calibration_sets/<time>/`.

| file | holds |
|---|---|
| `blocks.json` | the first and last time of each calibration block, as [blocks.schema.json](../../common/schemas/blocks.schema.json) describes |
| `calibration_rows.npy` | a True or False for every row of the grid, True where the row calibrates |
| `meta.json` | where the calibration set came from, as [meta.calibration_sets.schema.json](../../common/schemas/meta.calibration_sets.schema.json) describes |

## The blocks

| argument | what it decides |
|---|---|
| `share` | how much of the seconds above `min_speed` calibrates |
| `block` | how long one calibration block is, in seconds above `min_speed` |

The blocks are cut over the non-test rows alone, so the test span never phases them. A
block is measured in seconds above `min_speed`, as the log split is. Rows at or below
`min_speed` inside a block make it longer in time. They do not make it hold less. A
block is kept as the time of its first and last row.
