# train_set

Takes the training logs and returns one row every 100 ms, each with 17 columns, one
per decoded value, such as `engine_speed` and `wheel_speed`. The test rows come from
[attack_set](attack_set.md).

```python
raw, t, seg = grid_rows(train_logs)     # the train half, from split.md
moving = raw[:, WHEEL] > MIN_SPEED
scale = scale_for(raw[train_rows & moving])   # train_rows from split_rows, in split.md
rows = scale.apply(raw[train_rows])
```

| name | what it holds |
|---|---|
| `raw` | the rows before scaling |
| `t` | the time of each row, in epoch seconds |
| `seg` | which unbroken run of rows it belongs to |
| `scale` | the mean and std that turn `raw` into `rows`, see [scale](scale.md) |

`raw` keeps every column in its own unit, for example `engine_speed` in rpm and
`wheel_speed` in km/h. That is what the rules read, since a rule is written in those
units. `rows` is what a model reads. A run of rows is unbroken while each one is
100 ms after the one before, which [grid](grid.md) sets out.

## Stopped rows are kept

Many rows are stopped or idling. They stay in `rows`, since dropping them would break
the segments [grid](grid.md) describes.

The mean and std are taken only over the rows [evaluate](../../evaluate) scores,
because those are the rows PCA is fitted on. Stopped rows spread some signals far
wider than moving ones do, such as `clutch_slip` and `input_shaft_speed`. With them in
the std, those signals would count for less in the residual than the others.
