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
scored as fit trains and scores rows, with the same `models.autoencoder.fit`. It is
trained on the error over all `rows` × 17 values. Its score is the mean squared error
over the 17 values of the last row only.

```python
flat = windows.reshape(len(windows), -1)   # (windows, rows * signals)
net = NonlinearAutoencoder(signals=rows * signals, latent_dim=k, hidden=hidden)
losses = fit(flat, net, epochs=epochs, batch=batch, rate=rate,
             threshold=improvement, patience=patience)
```

## The window delta ae

A window delta ae is the window nonlinear ae on the steps between the rows of a window
rather than on the rows. Its network, `DeltaAutoencoder`, takes the step from each row
to the next, divides each signal's step by `step_std`, and reconstructs the `rows - 1`
steps with a nonlinear autoencoder. Its score is the mean squared error over the 17
values of the last step.

`step_std` is each signal's std of the steps over the windows it is fitted on, taken
before the fit. The rows are scaled already, but a signal that moves little from row
to row would still give steps too small to count in the error without it. It is kept
with the tensors under `window_delta_ae.r{rows}.h{hidden}.k{k}.`.

The network returns the window with the error of each step added. So its output less
its input is that error, and fit, scoring and the ONNX export treat it as they treat a
window nonlinear ae. A delta ae is the same in the ONNX file, the steps and `step_std`
included.

It was added to catch a signal held still or repeated with noise, whose rows each look
normal. Whether it does was not measured when it was added.

A window delta ae is fitted on one window every `stride` rows. Two windows next to each
other share all but one row, so a `stride` above 1 cuts the memory and the time of the
fit while leaving out little. What it leaves out was not measured. It is scored and
calibrated on every window, as the board scores it.

## The window drift ae

A window drift ae is the window delta ae on how far each row of a window sits from its
first row rather than on the steps. Its network, `DriftAutoencoder`, takes each row less
the first, divides each value by `drift_std` for its row and signal, and reconstructs
the `rows - 1` rows. Its score is the mean squared error over the 17 values of the last
row, how far the window moved in all.

`drift_std` is each value's std over the windows it is fitted on, taken before the fit.
A row further from the first moves further on a normal drive, so each row has its own.
It is kept with the tensors under `window_drift_ae.r{rows}.s{stride}.h{hidden}.k{k}.`.
It is fitted on one window every `stride` rows, and its network returns the window
with its error added, as the window delta ae does.

## The window conv1d ae

A window conv1d ae is the window delta ae with 1D convolutions along time in place of
dense layers. Its network, `Conv1dAutoencoder`, takes the same scaled steps, the `rows
- 1` steps as a time series of 17 channels. Two convolutions of 5 rows and stride 2
take them to `hidden` and then `k` channels, each a quarter as long in time, and two
transposed convolutions take them back. Its score is the error over the 17 values of
the last step, as for the window delta ae.

The convolutions share their weights along time, so the weights do not grow with
`rows`. At `hidden` 32 and `k` 8 it holds 8,089 weights at any `rows`. Its tensors are
kept under `window_conv1d_ae.r{rows}.s{stride}.h{hidden}.k{k}.`.

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
