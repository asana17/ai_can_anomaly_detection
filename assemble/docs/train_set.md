# train_set

Takes the training logs and returns one row every 100 ms, each with 17 columns, one
per decoded value, such as `engine_speed` and `wheel_speed`. The test rows come from
[attack_set](attack_set.md).

```python
data = scaled_rows(train_logs)     # the train half, from split.md
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
100 ms after the one before, which [grid](grid.md) sets out.

`save` writes each key to `out/<key>.npy`, and `scale` as `mean.npy` and `std.npy`.

## Why the scale comes back

[attack_set](attack_set.md) builds the test rows and has to scale them with the
`scale` fitted here, on the train logs. Fitting one from the test rows would put them
in different units from the rows a model was fitted on.

## Stopped rows are kept

Over half the rows are stopped or idling. They stay in, and the mean and std are
taken over them too. Dropping them would break the segments [grid](grid.md)
describes, and leaving them out changes each signal's spread by less than half.
