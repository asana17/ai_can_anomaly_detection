# gear_ratio

Flags the engine and wheel speeds not matching the gear the transmission reports.

```python
violations(values, ratios=RATIOS, min_speed=5.0)   # -> the three names, or empty
nearest_gear(ratio)                                # -> the gear that ratio belongs to
```

Each gear turns the engine a set number of times per km/h, and the gears are 1.28
apart, so a measured ratio picks out one of them. The rule asks whether that is the
reported gear. There is no tolerance to choose, only the table.

That works because the spread inside a gear stays smaller than the distance to its
neighbour. Top gear sits within 1.7% of its own ratio and 12.8% from the next one.
Low gears are looser, up to 22%, and still land on themselves.

## Where it stays quiet

Mid shift the ratio is undefined, so the rule waits until the reported and selected
gears agree. With the clutch open the engine is not tied to the wheels at all, so it
waits for a slip of zero. Under 5 km/h the wheel speed is too coarse, as in
[shaft_ratio](shaft_ratio.md).

Inside those gates it picks the wrong gear on 0.0080% of evaluations, 12 of 150,291,
measured in [measurements](../../docs/measurements.md).

Gears 1 and 3 are missing from the table, too rare in the data to place, so a report
of either is not checked. Their absence also leaves gear 2 with no near neighbour,
which makes its check the loosest of the ten.
