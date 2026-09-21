# export

The board runs C code that ST Edge AI Core generates from an ONNX file. `export` takes
every nonlinear autoencoder [fit](../../evaluate/docs/fit.md) wrote, writes each one
out as float ONNX for that, and keeps them in the runs repository.

## Running it

```
python3 -u -m deploy.export runs_repo revision models/<time> runs_dir [--rebuild]
```

| argument | what it is |
|---|---|
| `runs_repo` | Hugging Face model repo holding the models and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the models at, as [fit](../../evaluate/docs/fit.md) printed it |
| `models/<time>` | the fitted models to export |
| `runs_dir` | local folder the models are downloaded to and `onnx/<time>/` is written to |
| `--rebuild` | export again even if `runs_repo` already holds a directory with the same `inputs` |

Limitation: only the nonlinear autoencoders are exported. Every one in the models
directory is written.

## What it writes

It writes these files into `runs_dir/onnx/<time>/` and uploads that directory to
`runs_repo` as `onnx/<time>/`.

| file | holds |
|---|---|
| `nonlinear_ae_k{k}_h{h}_float.onnx` | one file per model, in float32 |
| `meta.json` | where the models came from, and which models were written, as [meta.onnx.schema.json](../../common/schemas/meta.onnx.schema.json) describes |

## Versions

ONNX 1.16.2, the one ST Edge AI Core 4.0.1 bundles.
