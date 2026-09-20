# split

`split` cuts the logs into train and test. The training rows are cut into train and
calibration rows by [train_set](train_set.md).

## Example

```python
seconds = seconds_above(logs, min_speed)      # from seconds.md
# the logs are cut into n_splits blocks by time, and block number fold becomes test
train_logs, test_logs = split(seconds, n_splits, fold)
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

So the cut is made on the seconds above `min_speed`. [seconds](seconds.md) counts them
one log at a time, giving 0 for a log the truck sat still through and the log's whole
length for one it drove right through.

