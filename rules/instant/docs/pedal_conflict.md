# pedal_conflict

Flags the accelerator and the brake being pressed at once.

```python
hits(raw, pressed=1.0)   # -> True per row the rule fires on
```

Over every log both read pressed on 1,066 of the 2,757,787 moving grid rows, drivers
holding both pedals, measured in [measurements](../../measurements.md). A pedal
resting on its stop reports a little above zero, so neither counts as pressed until
it clears 1%.

The brake is pressed at all on 9.30% of moving grid rows, so this can only fire in
that fraction of the time.
