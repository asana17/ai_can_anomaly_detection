# datasets

Turns a chronological log split into the arrays the autoencoder trains on. Each
row is one grid tick of the signals, and the z-score is fit on train alone, then
reused for validation and test so no future data leaks into the scaling.

```python
logs = sorted(glob("data/part_*/*.csv"))      # every log, oldest first
train, test = split(logs, 0.75, driving_time(logs))
train, val = hold_out(train, 0.07, blocks=5, gap=1)
data = scaled_rows(train, val, test, period=0.1, max_hold=1.0)
save(data, "out")
```

`scaled_rows` returns each split as an array of shape `(rows, signals)`, plus the
`Scale` fitted on train. `<split>_raw` holds the same rows before scaling, which is
what the rules read. `save` writes all of it as `.npy` files.

`Scale` carries the `mean` and `std` together, and `apply` and `undo` are the only
places rows move between the two. [attack_set](attack_set.md) builds its rows
separately and has to be handed the same one, or its rows land on a different scale
from the ones the model was fitted on.

The z-score lives here rather than in [preprocess](../../preprocess), because a
`Scale` is fitted on train the way the model's own parameters are, and only this side
knows which logs those are.

`period` and `max_hold` go straight through to
[grid_sample](../../preprocess/docs/grid_sample.md), which documents what they mean
and why they default to 100 ms and 1 second.

## Every row is kept, not every row is scored

Over half the rows are stopped or idling. They stay in. Dropping them would break
the segments below, and fitting the z-score without them moves each signal's spread
by less than half.

The model scores only rows above 5 km/h, where the residual keeps one shape and a
threshold carries. Below it the ground belongs to
[engine_off](../../rules/instant/docs/engine_off.md),
[stopped_shaft](../../rules/instant/docs/stopped_shaft.md) and
[pedal_conflict](../../rules/instant/docs/pedal_conflict.md).

## Times and segments

Each split also comes with `<split>_t`, the time of every row, and `<split>_seg`,
its segment id. Times are what a synthesized attack window is matched against to
label the rows it covers.

A segment is a run of rows one `period` apart. Segments break between logs and
wherever the grid restarted after a gap in the recording, so only rows of one
segment may go into a time window. A window that spanned a break would present a
jump of hours as a transition of 100 ms, and a model reading time would learn it
as one.

Ids are numbered within a split and so repeat between splits, which the splits
being disjoint sets of logs makes harmless.
