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
grid_rows_injected(inject_frames(logs, rng, source_logs), rows_before_attack,
                   period=period, max_hold=max_hold)
# -> {raw, t, seg, label, wheel, attacks}
```

It takes what `inject_frames` yields rather than drawing the attacks itself, so the
frames can go somewhere else on the way. `rows_before_attack(log)` gives that log's
rows by time as they were before the attack, which a [grid](grid.md) holds already. It
raises on a log whose rows line up with none of them, which is what a grid built on
another `period` looks like.

`attacked_log` does one log and `grid_rows_injected` lays the logs end to end, moving
each attack's rows and each log's segment ids along as it goes.

| key | what it holds |
|---|---|
| `raw` | the rows, in the units they are decoded to |
| `t` | the time of each row |
| `seg` | the segment each row belongs to, numbered as [grid](grid.md) describes |
| `label` | True where the row differs from the same row before the attack |
| `wheel` | the wheel speed before the attack |
| `attacks` | what was faked, its log, and the first and last row it reaches |

`label` is never True across the whole attack window, only where a row changed.

Putting the rows on the [scale](scale.md) is for whoever scores them, as is measuring
how far an attack moved a row in those units. [evaluate](../../evaluate) scores only
the attacks that moved one by at least `MOVED`, so an attack that changed nothing a
model could see is not counted as a miss.

[evaluate](../../evaluate) uses `wheel` to decide whether a row is scored. So an attack
that fakes a stop still leaves the scored rows the same as with no attack.

`raw` is what the rules read. Reconstructing it from `rows` instead loses enough
precision that engine_load at its ceiling of 250 comes back as 250.0000009, and
range_check calls that out of range on 15% of ordinary rows.

Every log contributes its rows, including the ones no attack landed in. What comes
back is the whole test period with attacks in it, not a set of attacked rows.

## Rules are not applied here

This returns the data. [evaluate](../../evaluate) is where the rules run.
