# grid

[datasets](datasets.md) and [attack_set](attack_set.md) each build rows. They have to
use the same settings. The settings are here.

## The grid

| name | value | what it is |
|---|---|---|
| `PERIOD` | 0.1 s | the time between two rows |
| `MAX_HOLD` | 1 s | the longest gap between frames a row may be built across |

Both come from [grid_sample](../../preprocess/docs/grid_sample.md).

## Types

Rows are `float32`, times `float64`, segments `int32`. Times are epoch seconds, near
1.6e9, where `float32` steps in units of 128 seconds.

## Segments

`seg` is the segment id of each row. It changes at a log boundary and after a gap in
the recording.
