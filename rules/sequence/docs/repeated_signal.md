# repeated_signal

Flags a signal that reads what it read ten rows before, on each of the last ten moving
rows.

```python
hits(raw, position)   # -> True where a WATCHED signal repeated LAG rows back over ROWS rows
LAG                   # -> 10, one second
ROWS                  # -> 10
WATCHED               # -> engine_speed, input_shaft_speed, yaw_rate, lateral_accel
```

A stretch of the bus sent again reads the same values a stretch later. These four
signals move a little on every row, so on a normal drive they do not come back to
exactly the same values. A NaN never counts as the same.

## How it was picked

Measured over every log on grid `20260925-201019`, 2,757,787 moving rows. The rows each
signal read what it read ten rows before, on each of five and ten rows.

| signal | 5 rows | 10 rows |
|---|---|---|
| engine_speed | 0 | 0 |
| input_shaft_speed | 1 | 0 |
| yaw_rate | 4 | 0 |
| lateral_accel | 0 | 0 |
| wheel_speed | 6,304 | 180 |
| tachograph_speed | 6,204 | 152 |
| output_shaft_speed | 1,960 | 52 |
| steering_angle | 639 | 3 |

Those counts leave out the rows the signal held one value over, which
[frozen_signal](frozen_signal.md) judges. The rule itself does not, so it fires on a
held value too.

It fires on no row. The rules together fire on the same 1,945 rows as with
frozen_signal alone.

## What it misses

It compares with ten rows back only. A stretch of 1, 2, 5 or 10 rows sent again reads
the same ten rows later and fires. A stretch of another length, such as 8 rows, does
not.

## Where it came from

It was thought of after `repeated_replay` in [replay](../../../attack/docs/replay.md)
was built. The signals, the lag and the rows come from normal data alone.
