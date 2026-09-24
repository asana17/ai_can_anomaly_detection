# engine_off

Flags the engine reading stopped while something it drives is still running.

```python
hits(raw)      # -> True per row the rule fires on
MUST_BE_ZERO   # -> the names that must read zero with it
```

A stopped engine burns no fuel and makes no torque. The input shaft is left out. Over
every log it still turns at 100 to 312 rpm on 139,318 of 36,041,922 evaluations with
the engine at zero. Without it the rule fires on 1,836 of them, and on none of the
moving grid rows.

The ratio rules all need the truck moving and say nothing here. This one works while
the truck is stopped.
