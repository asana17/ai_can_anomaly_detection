# attack_set

Injects one attack into each test log, then puts the frames on the grid and says which
rows each attack changed.

## Injecting the frames

```python
inject_frames(logs, rng, source_logs)
# -> (path, frames, hurt, span) per log
```

One attack per log, chosen by [inject](../../attack/docs/inject.md). `inject_frames`
does the injection and yields each log's frames before and after the attack, so
anything that needs the attacked frames gets the same attacks from the same random
generator, `rng`.

A replay can copy a value close to the one it replaced. The result is a row the bus
really produces, and no detector should be asked to flag it.

## Building the rows

```python
grid_rows_injected(logs, scale, rng, source_logs)
# -> {rows, raw, t, seg, label, wheel, attacks}
```

`scale` is the one [train_set](train_set.md) fitted on the training rows. See
[scale](scale.md).

| key | what it holds |
|---|---|
| `rows` | the rows on `scale` |
| `raw` | the same rows before scaling |
| `t` | the time of each row |
| `seg` | the segment each row belongs to, numbered as [grid](grid.md) describes |
| `label` | True where the row differs from the same row before the attack |
| `wheel` | the wheel speed before the attack |
| `attacks` | what was faked, the first and last row it reaches, and `moved` |

`label` is never True across the whole attack window, only where a row changed.
`moved` is the furthest the attack pushed any row in z units.
[evaluate](../../evaluate) scores only attacks with `moved` of at least 1, so one
that changed nothing is not counted as a miss.

[evaluate](../../evaluate) uses `wheel` to decide whether a row is scored. So an attack
that fakes a stop still leaves the scored rows the same as with no attack.

`raw` is what the rules read. Reconstructing it from `rows` instead loses enough
precision that engine_load at its ceiling of 250 comes back as 250.0000009, and
range_check calls that out of range on 15% of ordinary rows.

Every log contributes its rows, including the ones no attack landed in. What comes
back is the whole test period with attacks in it, not a set of attacked rows.

## Rules are not applied here

This returns the data. [evaluate](../../evaluate) is where the rules run.
