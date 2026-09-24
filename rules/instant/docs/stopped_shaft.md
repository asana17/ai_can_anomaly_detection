# stopped_shaft

Flags the transmission output shaft turning while both speeds report stopped.

```python
hits(raw, max_shaft=50.0)   # -> True per row the rule fires on
```

The output shaft and the wheels turn together, so one cannot move while the other
sits still. [shaft_ratio](shaft_ratio.md) checks the same thing but only above
20 km/h, so nothing checks it while the truck is stopped.

The limit sits at 50 rpm rather than 0. Over every log the shaft reads up to 551 rpm
with the wheels at zero, and above 50 on 2,600 of 106,072,217 evaluations, where the
tachograph speed shows the truck still rolling. So the tachograph has to read zero
too, and then the rule fires on 110. A wheel speed at zero against a rolling
tachograph is left to [speed_agreement](speed_agreement.md).
