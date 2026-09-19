# split

`split` cuts the logs into train and test. `split_rows` cuts the training rows into
train and calibration rows.

## Example

```python
seconds = seconds_above(logs, min_speed)
train_logs, test_logs = split(seconds, n_splits, fold)   # block `fold` of `n_splits` is test

raw, t, seg = grid_rows(train_logs)             # from train_set.md
train_rows, calibration_rows = split_rows(raw, t, share, block, gap, min_speed)
```

## Running it

```
python3 -m assemble.split repo revision seconds/<time> local_dir [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `seconds/<time>/` and uploaded to, needs `hf auth login` |
| `revision` | commit of `repo` to read `seconds/<time>/` at, as [seconds](seconds.md) printed it |
| `seconds/<time>` | the [seconds](seconds.md) directory to cut on |
| `local_dir` | local folder `splits/<time>/` is written to, kept after the upload |
| `--rebuild` | cut even if `repo` already has `splits/<time>/` for the same `seconds/<time>`, `N_SPLITS` and `FOLD` |

It writes these two files into `local_dir/splits/<time>/` and uploads that directory to
`repo` as `splits/<time>/`.

| file | holds |
|---|---|
| `split.json` | `train` and `test`, the logs of each, keyed by path relative to the logs' folder |
| `meta.json` | `inputs` (`seconds/<time>`, `N_SPLITS`, `FOLD`), `seconds` (repo, revision, path), commit, uncommitted files, start, end |

## Train and test are sized by the seconds above the minimum speed

Only rows above `min_speed` are scored, and only they set the threshold. Everything
slower is left to the rules.

The truck is parked for long runs of consecutive logs, so a part chosen by log count
alone can hold no scoreable row at all.

So the cut is made on the seconds above `min_speed`. `seconds_above` counts them one
log at a time, giving 0 for a log the truck sat still through and the log's whole length
for one it drove right through.

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
