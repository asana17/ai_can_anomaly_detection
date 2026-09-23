# gear_ratio

Flags the engine and wheel speeds not matching the gear the transmission reports.

```python
hits(raw, min_speed, ratios=RATIOS)   # -> True per row the rule fires on
nearest_gear(ratio)                   # -> the gear each ratio belongs to
```

Each gear turns the engine a set number of times per km/h, and the gears are 1.26 to
1.30 apart, so a measured ratio picks out one of them. The rule asks whether that is
the reported gear. There is no tolerance to choose, only the table.

That works because the spread inside a gear stays smaller than the distance to its
neighbour. Over every log at p99, top gear sits within 0.9% of its own ratio and
fourth within 10.8%, while the boundary with the nearest gear lies 11.8% or more
away.

## Where it stays quiet

Mid shift the ratio is undefined, so the rule waits until the reported and selected
gears agree. With the clutch open the engine is not tied to the wheels at all, so it
waits for a slip of zero. Under 5 km/h the wheel speed is too coarse, as in
[shaft_ratio](shaft_ratio.md).

Inside those gates it picks the wrong gear on 0.0148% of evaluations, 317 of
2,134,856 gridded rows over every log. Half of them, 154, report fifth.

Gears 1 and 3 are missing from the table, too rare in the data to place, so a report
of either is not checked. Their absence also leaves gear 2 with no near neighbour,
which makes its check the loosest of the ten.
