# attack_set

Builds the test arrays with attacks in them, and says which rows each one changed.

```python
attack_set(logs, scale, rng, source_logs)   # -> {rows, raw, t, seg, label, attacks}
```

One attack per log, chosen by [inject](../../attack/docs/inject.md). `scale` is the
one [scaled_rows](datasets.md) fitted on train, so an attacked row lands on the same
scale as a normal one.

A replay can land on a value close to the one it replaced, leaving a row the bus
really produces that nothing can flag. `label` is therefore True where the attacked
row differs from the untouched one, not where the attack window falls. `attacks`
lists what was faked, the first and last row it reaches, and `moved`, the furthest it
pushed a row in z units. Both keep what changed nothing out of the miss count.

`raw` is the same rows before scaling, which is what the rules read. Reconstructing
them from `rows` instead loses enough precision that engine_load at its ceiling of 250
comes back as 250.0000009, and range_check calls that out of range on 15% of ordinary
rows.

Files where no attack landed still contribute their rows. The set therefore holds
normal traffic as well, which is what false alarms are counted against.

## Rules are not applied here

Which rules form the floor depends on what the models being compared can read, so
this returns the data and leaves that to the caller. See
[detection](../../rules/README.md) for the two kinds.
