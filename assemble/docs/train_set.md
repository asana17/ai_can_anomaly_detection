# train_set

`train_set` picks the rows a model is fitted on. They are what the
[calibration set](calibration_set.md) leaves of the non-test logs.

- A train row is from a non-test log and above `min_speed`.
- It is more than `gap` seconds from the test span and from every calibration block.
- No instant [rule](../../rules) hits it.

It writes only which rows those are. The rows stay in the [grid](grid.md).

## Running it

```
python3 -m assemble.train_set repo revision calibration_sets/<time> local_dir [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `calibration_sets/<time>/` and uploaded to, needs `hf auth login` |
| `revision` | commit of `repo` to read `calibration_sets/<time>/` at, as [calibration_set](calibration_set.md) printed it |
| `calibration_sets/<time>` | the calibration set whose blocks the train rows keep away from. The log split and grid it names are read too |
| `local_dir` | local folder `train_sets/<time>/` is written to, kept after the upload |
| `--rebuild` | build even if `repo` already has `train_sets/<time>/` for the same calibration set and `GAP` |

`MIN_SPEED` comes from the log split's `meta.json`, so the stages all use the one value.

It writes these files into `local_dir/train_sets/<time>/` and uploads that directory to
`repo` as `train_sets/<time>/`.

| file | holds |
|---|---|
| `train_rows.npy` | a True or False for every row of the grid, True where the row trains |
| `meta.json` | where the train set came from and how many train rows a rule hit, as [meta.train_sets.schema.json](../../common/schemas/meta.train_sets.schema.json) describes |

## Stopped rows stay in the grid

The grid keeps stopped rows. `HOLD` in [evaluate](../../evaluate) counts rows that are
next to each other in a `seg`, and two rows are only next to each other when they are
`period` apart. Dropping a stopped row would put two rows side by side that are not.

## Rows a rule hits are not fitted on

A model is only asked about the rows no instant rule hits, so it is fitted on those
alone. `rule_hits` is given the log split's `min_speed`.

## The gap

An event such as hard braking runs for seconds, long enough to cross the edge of a
calibration block or of the test span. So the rows within `gap` of either go to no
set. `seconds_from(times, spans)` is how far each row lies from the nearest span.
