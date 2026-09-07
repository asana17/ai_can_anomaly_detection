# engine_off

Flags the engine reading stopped while something it drives is still running.

```python
violations(values)   # -> engine_speed and whatever is moving, or empty
MUST_BE_ZERO         # -> the names that must read zero with it
```

A stopped engine burns no fuel, makes no torque, and turns no input shaft. All six
names in `MUST_BE_ZERO` read exactly zero across every stopped evaluation measured,
so the rule needs no threshold.

The ratio rules all need the truck moving and say nothing here. This one works while
the truck is stopped.
