# fit_windows

`fit_windows` reads a [train set](../../assemble/docs/train_set.md) and cuts its train
rows into windows. It fits every window model listed in a JSON file on them. It then
uploads the fitted models as `window_models/<time>/` of the runs repository.

It is apart from [fit](fit.md), so the models of `fit` are neither fitted again nor
changed. `--rebuild` of one leaves the other alone.

## Running it

```
python3 -m models.fit_windows repo revision train_sets/<time> local_dir runs_repo runs_dir [--models window_models.json] [--rebuild]
```

The arguments are those of [fit](fit.md#running-it). Without `--models` the list is
`models/window_models.json`.

| file | holds |
|---|---|
| `weights.safetensors` | every fitted model's tensors, and `scale.mean` and `scale.std` |
| `losses.json` | one entry per window nonlinear ae. A var is solved, so it has none |
| `meta.json` | what was fitted, and on what, as [meta.window_models.schema.json](../../common/schemas/meta.window_models.schema.json) describes |

A var's tensors are `var.r{rows}.coefficients` and `var.r{rows}.intercept`. A window
nonlinear ae's are those of the [nonlinear autoencoder](autoencoder.md) under
`window_nonlinear_ae.r{rows}.h{hidden}.k{k}.`.

## The window nonlinear ae

A window nonlinear ae is the nonlinear autoencoder of [fit](fit.md) on windows. Each
window is laid out oldest row first as one row of `rows` × 17 values. It is trained and
scored as fit trains and scores rows, with the same `models.autoencoder.fit`. Its score
is the mean squared error over all `rows` × 17 values.

```python
flat = windows.reshape(len(windows), -1)   # (windows, rows * signals)
net = NonlinearAutoencoder(signals=rows * signals, latent_dim=k, hidden=hidden)
losses = fit(flat, net, epochs=epochs, batch=batch, rate=rate,
             threshold=improvement, patience=patience)
```

## The windows it fits on

A window is `rows` train rows next to each other in one segment, oldest first. The
train set gives each train row its segment, a new one wherever a row between two
train rows was removed, so a window never joins rows that were apart. The cut is
[windows](../../preprocess/features/windows.py), the same rule the board uses.

```python
position = positions(moving(train_rows), segments)
ends = window_ends(position, rows=model.rows)
windows = window_rows(scaled_train_rows, ends, rows=model.rows)
```

Every window is fitted on, one ending at each train row that has `rows - 1` train rows
of its segment before it. Windows that hold a rule hit are kept. Rules and models meet in
detect alone.

The train rows are all moving rows, so a window holds no stopped row. A window that
holds a NaN is left out. A NaN is a value J1939 reserves, as in [fit](fit.md). The
window is left out, not cut short at the NaN, so the other windows stay where the
board places them.

The windows are cut again on every run and not stored. On the train set
`train_sets/20260926-152733`, with 1,759,645 train rows, the cut took under a second
for each `rows`, measured on 2026-09-27. That measurement cut the same windows out of the
whole grid with the train rows marked, not out of the train rows alone.

| `rows` | windows | size as float32 |
|---|---|---|
| 5 | 1,735,855 | 0.59 GB |
| 10 | 1,707,931 | 1.16 GB |
| 20 | 1,654,339 | 2.25 GB |

The memory a fit takes on top of the windows was not measured.

## The scale

The scale is that of [fit](fit.md#the-scale), taken from the train rows that hold no
NaN. It is applied to the train rows before the cut. Each value is scaled on its own,
so this gives the same windows as scaling each window.

## The models this repository fits

`models/window_models.json` asks for a [var](var.md) at `rows` 5, 10 and 20, and a
window nonlinear ae with `hidden` 128 at these `rows` and `k`. The window nonlinear ae
is fitted with the values of fit's autoencoder. They were chosen without looking at
any attack.

| `rows` | `k` |
|---|---|
| 5 | 12, 24 |
| 10 | 16, 32 |
| 20 | 24, 48 |

How long a window nonlinear ae takes to fit was not measured.
