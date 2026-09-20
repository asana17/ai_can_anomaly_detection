# grid

The frames of a log arrive at their own rates, so they are read into one row every
`PERIOD` seconds, each column holding the last value that signal carried.
`grid_rows(logs)` does that for whole logs, returning `raw`, `t` and `seg`.
[attack_set](attack_set.md) reads the frames it attacked the same way. Both follow the
settings here.

## The grid

| name | value | what it is |
|---|---|---|
| `PERIOD` | 0.1 s | the time between two rows |
| `MAX_HOLD` | 1 s | the longest gap between frames a row may be built across |

`PERIOD` is 100 ms because that is how often the slowest target PGNs, CCVS1 and
LFE1, arrive. A shorter one only repeats their last value across rows. `MAX_HOLD` is
ten of those arrivals. What `resample` does with the two is in
[grid_sample](../../preprocess/docs/grid_sample.md).

## Types

Rows are `float32`, times `float64`, segments `int32`. Times are epoch seconds, near
1.6e9, where `float32` steps in units of 128 seconds.

## Segments

`seg` is the segment id of each row. It changes at a log boundary and after a gap in
the recording.

## Moving rows

`moving(raw, min_speed)` is True where a row's `wheel_speed` is above `min_speed`.
