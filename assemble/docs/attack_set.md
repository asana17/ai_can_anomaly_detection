# attack_set

Builds the test arrays with attacks in them, and says which rows each one covers.

```python
attack_set(files, mean, std, rng)   # -> {rows, t, seg, label, attacks}
```

One attack per log, chosen by [inject](../../attack/docs/inject.md). `mean` and `std`
are the ones [build](datasets.md) fit on train, so an attacked row is scaled the same
way a normal one is.

`label` is True on the rows an attack covers. `attacks` lists what was faked and the
first and last row it reaches, which is what lets detection be counted per attack
rather than per row.

Files where no attack landed still contribute their rows. The set therefore holds
normal traffic as well, which is what false alarms are counted against.

## Rules are not applied here

Which rules form the floor depends on what the models being compared can read, so
this returns the data and leaves that to the caller. See
[detection](../../rules/README.md) for the two kinds.
