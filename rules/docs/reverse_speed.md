# reverse_speed

Flags the truck reporting reverse while moving faster than it can back up.

```python
violations(values, max_speed=10.0)   # -> both names, or empty
```

[gear_ratio](gear_ratio.md) only holds for forward gears, since its table has no
entry for reverse. So once the reported gear goes negative nothing else ties it to
the speed.

Reverse never exceeded 3.5 km/h over 87,245 evaluations, so the limit sits at 10.
The check only applies while reverse is reported, which is a narrow slice.
