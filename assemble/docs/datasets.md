# datasets

Turns a chronological file split into the arrays the autoencoder trains on. Each
row is one grid sample of the signals, and the z-score is fit on train alone, then
reused for validation and test so no future data leaks into the scaling.

```python
files = sorted(glob("data/part_*/*.csv"))     # every log, oldest first
train, val, test = split(files, 0.70, 0.05)
data = build(train, val, test, period=0.1, max_hold=1.0)
save(data, "out")
```

`build` returns each split as an array of shape `(rows, signals)`, plus the `mean`
and `std` fit on train. `save` writes them, and the stats, as `.npy` files for the
model.

`period` and `max_hold` go straight through to
[grid_sample](../../preprocess/docs/grid_sample.md), which documents what they mean
and why they default to 100 ms and 1 second.

## Every row is kept

A stopped truck accounts for over half the rows, 16.7% with the engine off and 37.9%
idling. They stay in.

They are not the same row repeated. Over 30 files the engine off rows hold 502
distinct vectors, since the gear, the steering and the rest still report while the
engine does not. Fitting the z-score on all rows rather than the moving ones changes
each signal's spread by less than half, so keeping them does not distort the scaling.

Dropping them would also hide the ground three rules watch.
[engine_off](../../rules/instant/docs/engine_off.md),
[stopped_shaft](../../rules/instant/docs/stopped_shaft.md) and
[pedal_conflict](../../rules/instant/docs/pedal_conflict.md) only ever fire while the
truck is not moving.

## Times and segments

Each split also comes with `<split>_t`, the time of every row, and `<split>_seg`,
its segment id. Times are what a synthesized attack window is matched against to
label the rows it covers.

A segment is a run of rows one `period` apart. Segments break between files and
wherever the grid restarted after a gap in the recording, so only rows of one
segment may go into a time window. A window that spanned a break would present a
jump of hours as a transition of 100 ms, and a model reading time would learn it
as one.

Ids are numbered within a split and so repeat between splits, which the splits
being disjoint sets of files makes harmless.
