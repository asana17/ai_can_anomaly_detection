# train_set

[split](split.md) cuts the logs into train and test. This cuts the rows of the train
logs again.

- Train rows are the rows a model is fitted on.
- Calibration rows are the rows its threshold is read off.
- Some rows fall into neither.
- A row an instant [rule](../../rules) hits is never a train row.
- A calibration row may be one a rule hits.

It writes only which rows those are. The rows stay in the [grid](grid.md). The test
logs are [attack_set](attack_set.md)'s.

```python
training = rows_of_logs(logs, counts, train_logs)   # logs and counts from grid.md
train_rows, calibration_rows = split_rows(raw[training], t[training], share=share,
                                          block=block, gap=gap, min_speed=min_speed,
                                          period=period)
train_rows &= moving(raw, min_speed=min_speed)
train_rows[train_rows] = ~rule_hits(raw[train_rows], settings)
```

## Running it

```
python3 -m assemble.train_set repo revision splits/<time> local_dir [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `splits/<time>/` and uploaded to, needs `hf auth login` |
| `revision` | commit of `repo` to read `splits/<time>/` at, as [split](split.md) printed it |
| `splits/<time>` | the [split](split.md) directory whose train logs are taken. The grid it names is read too |
| `local_dir` | local folder `train_sets/<time>/` is written to, kept after the upload |
| `--rebuild` | build even if `repo` already has `train_sets/<time>/` for the same split, `CALIBRATION`, `BLOCK` and `GAP` |

`MIN_SPEED` comes from the split's `meta.json` and `PERIOD` from the grid's, so the
stages all use the one value.

It writes these files into `local_dir/train_sets/<time>/` and uploads that directory to
`repo` as `train_sets/<time>/`.

| file | holds |
|---|---|
| `train_rows.npy`, `calibration_rows.npy` | a True or False for every row of the grid, True where the row trains or calibrates. A row in neither is False in both, as is every test row |
| `meta.json` | where the train set came from and how many train rows a rule hit, as [meta.train_sets.schema.json](../../common/schemas/meta.train_sets.schema.json) describes |

## Stopped rows stay in the grid

The grid keeps stopped rows. `HOLD` in [evaluate](../../evaluate) counts rows that are
next to each other in a `seg`, and two rows are only next to each other when they are
`period` apart. Dropping a stopped row would put two rows side by side that are not.

## Rows a rule hits are not fitted on

A model is only asked about the rows no instant rule hits, so it is fitted on those
alone. Rows a rule hits stay in the calibration rows, as the rules are applied again
where they are scored. `rule_hits` is given the split's `min_speed`.

## The calibration set

The rows that set the threshold must be ones the model never saw. A model with enough
capacity fits its own training rows, so residuals on those come out smaller than on rows
it has not seen, and a threshold read off them would sit too low.

| argument | what it decides |
|---|---|
| `share` | how much of the seconds above `min_speed` calibrates |
| `block` | how long one calibration window is |
| `gap` | the seconds either side of a window that go to neither part |

An event such as hard braking runs for seconds, long enough to cross the edge of a
window and land on both sides of the split. That is what `gap` is for.

## The gap around the test block

An event can cross the edge of the test block as it crosses a calibration window.
`apart_from_test(times, start, end, gap)` drops the train rows within `gap` of the test
block, `start` and `end` being its first and last frame times.
