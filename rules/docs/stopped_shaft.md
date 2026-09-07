# stopped_shaft

Flags the transmission output shaft turning while the wheels report stopped.

```python
violations(values, max_shaft=50.0)   # -> both names, or empty
```

The output shaft and the wheels turn together, so one cannot move while the other
sits still. [shaft_ratio](shaft_ratio.md) checks the same thing but only above
5 km/h, so nothing checks it while the truck is stopped.

With the wheels reading zero the shaft still reads up to 31 rpm, so the limit sits at
50 rather than 0.
