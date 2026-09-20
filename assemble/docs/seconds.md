# seconds

Each log's seconds above `MIN_SPEED`, which [split](split.md) cuts on. They are counted
as the log's [moving](grid.md) rows on the grid, the rows train_set and attack_set score.

## Running it

```
python3 -m assemble.seconds data_dir "part_*/*.csv" local_dir repo [--rebuild]
```

| argument | |
|---|---|
| `data_dir` | local folder holding the CAN frame logs |
| `pattern` | glob of the logs to measure, relative to `data_dir`, e.g. `"part_*/*.csv"` |
| `local_dir` | local folder `seconds/<time>/` is written to, kept after the upload |
| `repo` | Hugging Face dataset repo to upload to, needs `hf auth login` |
| `--rebuild` | measure even if `repo` already has `seconds/<time>/` for the same logs and `MIN_SPEED` |

## What it uploads

It writes these two files into `local_dir/seconds/<time>/` and uploads that directory
to `repo` as `seconds/<time>/`.

| file | holds |
|---|---|
| `seconds.json` | seconds per log, keyed by the log's path relative to `data_dir` |
| `meta.json` | `inputs` (one SHA-256 over the logs' paths and sizes, their count, `MIN_SPEED`), commit, uncommitted files, start, end |
