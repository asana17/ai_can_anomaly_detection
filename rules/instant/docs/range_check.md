# range_check

Flags a signal outside the range J1939 defines for it.

```python
hits(raw)   # -> True per row with a signal outside its range
LIMITS      # -> {name: (minimum, maximum)}
```

The limits come from [spn_spec](../../../preprocess/docs/spn_spec.md). They are
compared as float32, the type a grid row holds, so the lowest decodable value of
steering_angle, yaw_rate and lateral_accel still passes.

Across 100 logs this fires on none of 5,034,836 decoded values, measured in
[measurements](../../measurements.md). Anything it reports is either an attack
or a decode that needs fixing.
