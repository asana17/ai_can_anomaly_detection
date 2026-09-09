# datasets

Reads a list of logs and returns one row every 100 ms. Each row has 17 columns,
one per decoded value, such as `engine_speed` and `wheel_speed`.

```python
data = scaled_rows(train, period=0.1, max_hold=1.0)
save(data, "out")
```

| key | what it holds |
|---|---|
| `rows` | the z-scored rows |
| `raw` | the same rows before scaling |
| `t` | the time of each row, in epoch seconds |
| `seg` | which unbroken run of rows it belongs to |
| `scale` | the mean and std that turn one into the other |

`raw` keeps every column in its own unit, for example `engine_speed` in rpm and
`wheel_speed` in km/h. That is what the rules read, since a rule is written in those
units. `rows` is what a model reads. A run of rows is unbroken while each one is
100 ms after the one before, which [Segments](#segments) sets out.

`save` writes each key to `out/<key>.npy`, and `scale` as `mean.npy` and `std.npy`.

`period` is the spacing of the grid and `max_hold` the longest gap it carries
across, 100 ms and 1 second. See [grid_sample](../../preprocess/docs/grid_sample.md).

## Why the scale comes back

The test rows are not built here. [attack_set](attack_set.md) builds them, with
attacks injected into the frames first, and it has to scale them by these same
numbers. Fitting its own would put its rows on a different scale from the ones the
model was fitted on.

`period` and `max_hold` have to match there too. Nothing checks it, so
[evaluate](../../evaluate) passes one pair to both.

## Stopped rows are kept

Over half the rows are stopped or idling. They stay in, and the mean and std are
taken over them too. Dropping them would break the segments below, and leaving them
out changes each signal's spread by less than half.

## Segments

Inside one log the rows are continuous, one `period` apart. Between logs, and across
a gap in the recording, they are not. `seg` numbers each continuous stretch, so two
neighbouring rows in the array can be hours apart unless they share a `seg`.

Anything that reads a row against the one before it has to check `seg` first.
