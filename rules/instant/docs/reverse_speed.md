# reverse_speed

Flags the truck reporting reverse while moving faster than it can back up.

```python
hits(raw, max_speed=10.0)   # -> True per row the rule fires on
```

[gear_ratio](gear_ratio.md) only holds for forward gears, since its table has no
entry for reverse. So once the reported gear goes negative nothing else ties it to
the speed.

The limit sits at 10 km/h. Over every log reverse reads up to 38.3 km/h, in 9 runs
where the gear stays at -1 while the truck drives off, and the rule fires on those, 9
of the 2,757,787 moving grid rows. The check only applies while reverse is reported,
which is a narrow slice.
