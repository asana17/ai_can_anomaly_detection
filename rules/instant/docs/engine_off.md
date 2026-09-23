# engine_off

Flags the engine reading stopped while something it drives is still running.

```python
hits(raw)      # -> True per row the rule fires on
MUST_BE_ZERO   # -> the names that must read zero with it
```

A stopped engine burns no fuel, makes no torque, and turns no input shaft. Over every
log the rule fires on 141,110 of 36,041,922 evaluations with the engine at zero, and
139,318 of those are the input shaft still turning at 100 to 312 rpm. None of them is
a moving grid row, so the evaluation does not see them.

The ratio rules all need the truck moving and say nothing here. This one works while
the truck is stopped.
