# train_set

[split](split.md) cuts the logs into train and test. This cuts the train logs' rows
again, into the rows a model is fitted on and the rows its threshold is read off, and
fits the [scale](scale.md) on the first of the two. Some rows fall into neither. It
writes only which rows those are, the rows stay in the [grid](grid.md). The test logs
are [attack_set](attack_set.md)'s.

```python
training = rows_of_logs(logs, counts, train_logs)   # logs and counts from grid.md
train_rows, calibration_rows = split_rows(raw[training], t[training], share=share,
                                          block=block, gap=gap, min_speed=min_speed,
                                          period=period)
scale = scale_for(raw[train_rows & moving(raw, min_speed=min_speed)])
rows = scale.apply(raw[train_rows])
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
| `scale.npy` | the mean and std, fitted on the moving train rows |
| `meta.json` | `inputs` (`splits/<time>`, `CALIBRATION`, `BLOCK`, `GAP`), `split` and `grid` (repo, revision, path), commit, uncommitted files, start, end |

## The scale is fitted on the moving train rows

The mean and std are taken only over the rows [evaluate](../../evaluate) scores,
because those are the rows PCA is fitted on. Stopped rows spread some signals far
wider than moving ones do, such as `clutch_slip` and `input_shaft_speed`. With them in
the std, those signals would count for less in the residual than the others.

The grid keeps stopped rows. `HOLD` in [evaluate](../../evaluate) counts rows that are
next to each other in a `seg`, and two rows are only next to each other when they are
`period` apart. Dropping a stopped row would put two rows side by side that are not.

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
