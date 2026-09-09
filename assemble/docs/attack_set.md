# attack_set

Builds the test arrays with attacks in them, and says which rows each one changed.

```python
attack_set(logs, scale, rng, source_logs)   # -> {rows, raw, t, seg, label, attacks}
```

One attack per log, chosen by [inject](../../attack/docs/inject.md).

`scale` is the mean and std [train_set](train_set.md) fitted on the training rows.
Passing anything else puts these rows in different units from the ones a model was
fitted on.

A replay can copy a value close to the one it replaced. The result is a row the bus
really produces, and no detector should be asked to flag it.

`label` is True only where the attacked row differs from the untouched one, never
across the whole attack window. `attacks` lists what was faked, the first and last
row it reaches, and `moved`, the furthest it pushed any row in z units.
[evaluate](../../evaluate) scores only attacks with `moved` of at least 1, so one
that changed nothing is not counted as a miss.

`seg` is the segment each row belongs to, numbered as [grid](grid.md) describes.

`raw` is the same rows before scaling, which is what the rules read. Reconstructing
them from `rows` instead loses enough precision that engine_load at its ceiling of 250
comes back as 250.0000009, and range_check calls that out of range on 15% of ordinary
rows.

Every log contributes its rows, including the ones no attack landed in. What comes
back is the whole test period with attacks in it, not a set of attacked rows.

## Rules are not applied here

This returns the data. [evaluate](../../evaluate) is where the rules run.
