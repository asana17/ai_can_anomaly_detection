# range_check

Flags a signal outside the range J1939 defines for it.

```python
violations(values)   # -> [name, ...] outside their range
LIMITS               # -> {name: (minimum, maximum)}
```

The limits come from [spn_spec](../../../preprocess/docs/spn_spec.md), so no threshold
is fitted here. Names with no definition are ignored, which lets a caller pass a
whole frame or a whole snapshot without filtering it first.

Across 100 files this fires on none of 5,034,836 decoded values, measured in
[measurements](../../measurements.md). Anything it reports is either an attack
or a decode that needs fixing.
