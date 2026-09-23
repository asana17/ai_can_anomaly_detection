# change_limit

Flags a signal moving faster than the truck can move it.

```python
violations(values, previous, seconds)   # -> the names that moved too far
LIMITS                                  # -> {name: most it may move per second}
```

The caller keeps the previous reading and the time since, which is what separates
this from the rules in [instant](../../instant). Both arguments come from the same
place, a decoded frame or a grid row, one step apart.

The signal being read and the one step before it have to sit in one segment.
[scoring](../../../scoring) checks that before calling, so nothing is compared
across a break in the recording.

## Which signals

Only four have a limit worth setting. The wheels and the two speeds are held by how
hard a truck can brake, and the steering and the yaw by how fast a driver can turn.

| signal | limit per second | most seen over 25 logs | over every log |
|---|---|---|---|
| yaw_rate | 3.0 rad/s2 | 1.1 | 5.6 |
| steering_angle | 40.0 rad/s | 16.4 | 36.3 |
| wheel_speed | 50.0 km/h/s | 21.0 | 374.8 |
| tachograph_speed | 100.0 km/h/s | 41.9 | 745.0 |

The rest move too freely to bound. A shift lets the input shaft spin to 670,000 rpm
per second, the clutch slip follows it, and the gear number jumps several places at
once. See [measurements](../../measurements.md).

## Timing

The limits are measured between one frame and the next of the same PGN, so they
belong with a rule running at frame arrival. A grid row is a different span, 100 ms
holding whatever arrived within it, and the same signal shows a slower rate there.
Reusing these numbers on grid rows would let real jumps through.

Over every log and 85,944,337 comparisons this fires 236 times, 149 on the yaw rate,
44 on the tachograph speed and 43 on the wheel speed.
