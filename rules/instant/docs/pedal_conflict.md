# pedal_conflict

Flags the accelerator and the brake being pressed at once.

```python
hits(raw, pressed=10.0)   # -> True per row the rule fires on
```

A pedal resting on its stop reports a little above zero, and drivers rest a foot on
both lightly, so neither counts as pressed until it clears 10%. Over every log both
read above 10% on 620 of the 2,757,787 moving grid rows, against 1,066 above 1%. On
the test set at a hold of 10 rows the rules raise 0.29 false alarms an hour against
0.57, and catch 483 attacks against 490, measured in
[measurements](../../measurements.md).

The brake is pressed at all on 9.30% of moving grid rows, so this can only fire in
that fraction of the time.
