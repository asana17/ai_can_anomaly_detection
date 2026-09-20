# grid

The frames of a log arrive at their own rates, so they are read into one row every
`period` seconds, each column holding the last value that signal carried.
`grid_rows(logs, period, max_hold)` does that for whole logs, returning `raw`, `t` and
`seg`. [attack_set](attack_set.md) reads the frames it attacked the same way.

## Running it

```
python3 -m assemble.grid data_dir "part_*/*.csv" local_dir repo [--rebuild]
```

| argument | |
|---|---|
| `data_dir` | local folder holding the CAN frame logs |
| `pattern` | glob of the logs to read, relative to `data_dir`, e.g. `"part_*/*.csv"` |
| `local_dir` | local folder `grids/<time>/` is written to, kept after the upload |
| `repo` | Hugging Face dataset repo to upload to, needs `hf auth login` |
| `--rebuild` | read them again even if `repo` already has `grids/<time>/` for the same logs, `PERIOD` and `MAX_HOLD` |

It writes these files into `local_dir/grids/<time>/` and uploads that directory to
`repo` as `grids/<time>/`.

| file | holds |
|---|---|
| `grid_{raw,t,seg}.npy` | every log read into rows, their times and segment ids |
| `logs.json` | the logs in the order they were read, and how many rows each contributed |
| `meta.json` | `inputs` (one SHA-256 over the logs' paths and sizes, their count, `PERIOD`, `MAX_HOLD`), commit, uncommitted files, start, end |

## The settings

| argument | what it decides |
|---|---|
| `period` | the time between two rows |
| `max_hold` | the longest gap between frames a row may be built across |

Both come from `Settings`, which every stage records in its `meta.json`. `period` is
100 ms because that is how often the slowest target PGNs, CCVS1 and LFE1, arrive. A
shorter one only repeats their last value across rows. `max_hold` is ten of those
arrivals. What `resample` does with the two is in
[grid_sample](../../preprocess/docs/grid_sample.md).

## Types

Rows are `float32`, times `float64`, segments `int32`. Times are epoch seconds, near
1.6e9, where `float32` steps in units of 128 seconds.

## Segments

`seg` is the segment id of each row. It changes at a log boundary and after a gap in
the recording.

## Moving rows

`moving(raw, min_speed)` is True where a row's `wheel_speed` is above `min_speed`.
