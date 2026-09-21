# range_check

Flags a signal outside the range J1939 defines for it.

```python
hits(raw)   # -> True per row with a signal outside its range
LIMITS      # -> {name: (minimum, maximum)}
```

The limits come from [spn_spec](../../../preprocess/docs/spn_spec.md), so no threshold
is fitted here.

Across 100 logs this fires on none of 5,034,836 decoded values, measured in
[measurements](../../measurements.md). Anything it reports is either an attack
or a decode that needs fixing.
