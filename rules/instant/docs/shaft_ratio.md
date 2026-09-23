# shaft_ratio

Flags the transmission output shaft turning at the wrong rate for the wheel speed.

```python
hits(raw, min_speed=20.0, bounds=(13.0, 17.5))   # -> True per row the rule fires on
```

The final drive and the tyre size are fixed, so the shaft turns a set number of
times per km/h whatever the gear or the engine is doing.

The ratio is 14.8 to 15.6 at motorway speed and widens as the wheel slows, so the
rule stays quiet below 20 km/h. Over the 2,757,787 moving grid rows of every log it
fires on 15 from 20 km/h, against 1,176 from 5 km/h, measured in
[measurements](../../measurements.md).
