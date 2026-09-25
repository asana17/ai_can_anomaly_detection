# change_limit

Flags a signal moving further in one tick than the truck can move it.

```python
hits(raw, previous)   # -> True where a row moved too far from the row before
LIMITS                # -> {name: most it may move per second}
```

The caller finds the row before, which is what separates this from the rules in
[instant](../../instant). It is kept out of `rule_hits`, the floor of the instant
pair, since the instant models do not see the row before.

## The row before

The row before is the row one tick earlier in the same grid segment, when that row
is moving too. Otherwise there is none, `previous` holds NaN, and the rule stays
silent. A hit does not end the run. This is the rule the board's row ring keeps, so
the PC and the board compare the same rows.

The time between the two is the tick, 0.1 s. A PGN sent every 100 ms can update 0 or
2 times between ticks, and the limits below are measured with that in.

## Which signals

Measured over every log on grid `20260922-093129`, 2,749,873 steps between two
moving rows. Each limit is a round figure above the 1e-5 quantile.

| signal | limit per second | 1e-5 | most |
|---|---|---|---|
| actual_engine_torque | 400 % | 360 | 490 |
| brake_pedal | 250 % | 212 | 360 |
| engine_speed | 2600 rpm | 2,509 | 2,825 |
| steering_angle | 10 rad/s | 9.39 | 11.1 |
| tachograph_speed | 40 km/h | 33.0 | 317 |
| wheel_speed | 40 km/h | 37.0 | 317 |
| yaw_rate | 0.4 rad/s2 | 0.364 | 0.488 |

The rest are not limited. accel_pedal, clutch_slip and the gears move their whole
range in one row. The input shaft is freed by a shift. The others were not tried. See
[measurements](../../measurements.md).

It fires on 87 steps. With the instant rules the rules fire on 1,713 of 2,757,787
moving rows, 0.0621%, under the 0.1% the rules are held to.
