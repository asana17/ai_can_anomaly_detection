# speed_agreement

Flags the two vehicle speeds disagreeing.

```python
hits(raw, limit=2.0)   # -> True per row the rule fires on
```

CCVS1 and TCO1 each report the vehicle's speed and they come from different senders,
so an attack that rewrites one PGN leaves the other alone. Neither reading has to
leave its own range for the pair to be wrong, which is what
[range_check](range_check.md) would miss.

The default limit of 2 km/h comes from the normal spread. Over every log the two sit
within 0.91 km/h of each other at p99 above 5 km/h, and more than 2 km/h apart on 587
of the 2,757,787 moving grid rows, measured in [measurements](../../measurements.md).

It reports nothing until both speeds have arrived, so a caller can pass a single
decoded frame and get an answer only once the state holds both.
