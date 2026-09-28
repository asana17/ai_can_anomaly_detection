# frozen_signal

Flags a signal that holds one value over the last ten moving rows.

```python
hits(raw, position)   # -> True where a WATCHED signal held one value over ROWS rows
ROWS                  # -> 10
WATCHED               # -> engine_speed, input_shaft_speed, yaw_rate, lateral_accel
```

These four signals move a little on every row while the truck moves, so a value that
stays exactly the same is one the bus did not measure. A NaN never counts as the same.

## How it was picked

Measured over every log on grid `20260925-201019`, 2,757,787 moving rows. The rows each
signal held one value over, for ten and twenty rows.

| signal | 10 rows | 20 rows |
|---|---|---|
| engine_speed | 0 | 0 |
| input_shaft_speed | 3 | 0 |
| yaw_rate | 0 | 0 |
| lateral_accel | 0 | 0 |
| wheel_speed | 15,439 | 1,825 |
| tachograph_speed | 15,413 | 1,808 |
| output_shaft_speed | 3,218 | 242 |
| steering_angle | 64,600 | 8,171 |

The speeds and the steering angle hold still at a steady speed or on a straight road,
so they are left out.

It fires on 3 rows. With the other rules the rules fire on 1,945 of 2,757,787 moving
rows, 0.0705%, under the 0.1% the rules are held to.

## Where it came from

It was thought of after `frozen_replay` in [replay](../../../attack/docs/replay.md) was
built. The signals and the rows come from normal data alone.
