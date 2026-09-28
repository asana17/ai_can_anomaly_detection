# export_windows

`export_windows` takes every window nonlinear autoencoder
[fit_windows](../../models/docs/fit_windows.md) wrote, writes each one out as float ONNX,
and keeps them in the runs repository. It does for the window models what
[export](export.md) does for the row models.

A window goes in as one row of `rows` × signals values, its oldest row first, as
fit_windows fits it.

## Running it

```
python3 -u -m deploy.export_windows runs_repo revision window_models/<time> runs_dir [--rebuild]
```

| argument | what it is |
|---|---|
| `runs_repo` | Hugging Face model repo holding the window models and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the window models at, as fit_windows printed it |
| `window_models/<time>` | the fitted window models to export |
| `runs_dir` | local folder the window models are downloaded to and `window_onnx/<time>/` is written to |
| `--rebuild` | export again even if `runs_repo` already holds a directory with the same `inputs` |

Limitation: the vector autoregressions are not exported. Every window nonlinear
autoencoder in the window models directory is written.

## What it writes

It writes these files into `runs_dir/window_onnx/<time>/` and uploads that directory to
`runs_repo` as `window_onnx/<time>/`.

| file | holds |
|---|---|
| `window_nonlinear_ae_r{rows}_k{k}_h{h}_float.onnx` | one file per model, in float32 |
| `meta.json` | where the models came from, and which models were written, as [meta.window_onnx.schema.json](../../common/schemas/meta.window_onnx.schema.json) describes |

## Versions

ONNX 1.16.2, the one ST Edge AI Core 4.0.1 bundles.
