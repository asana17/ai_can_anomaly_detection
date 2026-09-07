# pedal_conflict

Flags the accelerator and the brake being pressed at once.

```python
violations(values, pressed=1.0)   # -> both names, or empty
```

Never seen together in 486,544 evaluations, measured in
[measurements](../../docs/measurements.md). A pedal resting on its stop reports a
little above zero, so neither counts as pressed until it clears 1%.

The brake is pressed at all on 7.17% of moving evaluations, so this can only fire in
that fraction of the time. The zero says the two are never pressed together, not that
the check covers much.
