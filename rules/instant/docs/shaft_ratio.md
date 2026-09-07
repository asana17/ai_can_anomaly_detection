# shaft_ratio

Flags the transmission output shaft turning at the wrong rate for the wheel speed.

```python
violations(values, bounds=(13.0, 17.5), min_speed=5.0)   # -> both names, or empty
```

The final drive and the tyre size are fixed, so the shaft turns a set number of
times per km/h whatever the gear or the engine is doing.

The ratio is 14.8 to 15.6 at motorway speed and widens as the wheel slows. Below
5 km/h it spreads to 10 to 24, so the rule stays quiet there. Above that the default
bounds fire on 0.0073% of evaluations, measured in
[measurements](../../../docs/measurements.md).
