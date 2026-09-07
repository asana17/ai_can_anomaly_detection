# attack_set

Builds the test arrays with attacks in them, and says which rows each one changed.

```python
attack_set(files, mean, std, rng, source_logs)   # -> {rows, t, seg, label, attacks}
```

One attack per log, chosen by [inject](../../attack/docs/inject.md). `mean` and `std`
are the ones [build](datasets.md) fit on train, so an attacked row is scaled the same
way a normal one is.

A replay can land on a value close to the one it replaced, leaving a row the bus
really produces that nothing can flag. `label` is therefore True where the attacked
row differs from the untouched one, not where the attack window falls. `attacks`
lists what was faked, the first and last row it reaches, and `moved`, the furthest it
pushed a row in z units. Both keep what changed nothing out of the miss count.

Files where no attack landed still contribute their rows. The set therefore holds
normal traffic as well, which is what false alarms are counted against.

## Rules are not applied here

Which rules form the floor depends on what the models being compared can read, so
this returns the data and leaves that to the caller. See
[detection](../../rules/README.md) for the two kinds.
