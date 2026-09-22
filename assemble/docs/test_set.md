# test_set

Injects one attack into each test log, then puts the frames on the grid and says which
rows each attack changed.

## Running it

```
python3 -m assemble.test_set repo revision log_splits/<time> data_dir local_dir [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `log_splits/<time>/` and uploaded to, needs `hf auth login` |
| `revision` | commit of `repo` to read `log_splits/<time>/` at, as [split_test_logs](split_test_logs.md) printed it |
| `log_splits/<time>` | the [log split](split_test_logs.md) whose test logs are attacked. The grid it names is read too |
| `data_dir` | local folder holding the CAN frame logs the log split names |
| `local_dir` | local folder `test_sets/<time>/` is written to, kept after the upload |
| `--rebuild` | build even if `repo` already has `test_sets/<time>/` for the same log split, `SEED` and `DONORS` |

`PERIOD` and `MAX_HOLD` come from the grid's `meta.json`, so the rows land on the same
ticks as the grid's. The payloads are replayed from `DONORS` of the non-test logs,
spread evenly over those with seconds above `MIN_SPEED` in the log split's
`seconds.json`.

It writes these files into `local_dir/test_sets/<time>/` and uploads that directory to
`repo` as `test_sets/<time>/`.

| file | holds |
|---|---|
| `attacked_{raw,t,seg,label,wheel}.npy` | the test logs with the attacks in, on the grid |
| `injected.json` | each attack, its log, and the rows it reaches, as [injected.schema.json](../../common/schemas/injected.schema.json) describes |
| `frames/test-NNNNN.parquet` | the same logs frame by frame, as [injected_frames](injected_frames.md) writes them |
| `meta.json` | where the test set came from, as [meta.test_sets.schema.json](../../common/schemas/meta.test_sets.schema.json) describes |

## Injecting the frames

```python
injected = inject_frames(logs, rng, source_logs, rows_before_attack=rows_before_attack,
                         period=period, max_hold=max_hold, min_speed=min_speed)
# -> (path, frames, hurt, span) per log
```

At most one attack per log, chosen by [inject](../../attack/docs/inject.md). It copies
from the moving rows of one donor onto the moving rows of the log, the rows a model is
trained on. It lands only when every row it changed is moving before and after it, and
is not drawn again when it does not.

`inject_frames` does the injection and yields each log's frames before and after the
attack, so anything that needs the attacked frames gets the same attacks from the same
random generator, `rng`.

A replay can copy a value close to the one it replaced. The result is a row the bus
really produces, and no detector should be asked to flag it.

## Building the rows

```python
grid_rows_injected(injected, rows_before_attack, period=period, max_hold=max_hold)
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

Putting the rows on the [scale](../../preprocess/docs/scale.md) is for whoever scores
them, as is measuring how far an attack moved a row in those units.
[evaluate](../../evaluate) scores only the attacks that moved one by at least `MOVED`,
so an attack that changed nothing a model could see is not counted as a miss.

[evaluate](../../evaluate) uses `wheel` to decide whether a row is scored. So an attack
that fakes a stop still leaves the scored rows the same as with no attack.

`raw` is what the rules read. Reconstructing it from `rows` instead loses enough
precision that engine_load at its ceiling of 250 comes back as 250.0000009, and
range_check calls that out of range on 15% of ordinary rows.

Every log contributes its rows, including the ones no attack landed in. What comes
back is the whole test period with attacks in it, not a set of attacked rows.

## Rules are not applied here

This returns the data. [evaluate](../../evaluate) is where the rules run.
