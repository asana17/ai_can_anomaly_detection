# speed_agreement

Flags the two vehicle speeds disagreeing.

```python
violations(values, limit=2.0)   # -> both speed names, or empty
```

CCVS1 and TCO1 each report the vehicle's speed and they come from different senders,
so an attack that rewrites one PGN leaves the other alone. Neither reading has to
leave its own range for the pair to be wrong, which is what
[range_check](range_check.md) would miss.

The default limit of 2 km/h comes from the normal spread. The two sit within 0.9 km/h
of each other at p99 and more than 2 km/h apart on 0.006% of rows, measured in
[measurements](../../measurements.md).

It reports nothing until both speeds have arrived, so a caller can pass a single
decoded frame and get an answer only once the state holds both.
