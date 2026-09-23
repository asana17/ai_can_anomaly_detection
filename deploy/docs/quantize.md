# quantize

Quantize float onnx file [export](export.md) created to int8, and keep them in the runs
repository. [calibrate](../../models/docs/calibrate.md) with `--onnx-files` and
`--precision int8` gives each int8 file its threshold.

## Running it

```
python3 -u -m deploy.quantize runs_repo revision onnx/<time> runs_dir local_dir [--rebuild]
```

| argument | what it is |
|---|---|
| `runs_repo` | Hugging Face model repo holding the export and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the export at, as [export](export.md) printed it |
| `onnx/<time>` | the float onnx to quantize, which export step created |
| `runs_dir` | local folder the export is downloaded to and `quantize/<time>/` is written to |
| `local_dir` | local folder the train set the models name is downloaded to |
| `--rebuild` | quantize again even if `runs_repo` already holds a directory with the same `inputs` |

## What it writes

It writes these files into `runs_dir/quantize/<time>/` and uploads that directory to
`runs_repo` as `quantize/<time>/`.

| file | holds |
|---|---|
| `nonlinear_ae_k{k}_h{h}_int8.onnx` | one file per model, in int8 QDQ form, the input ST Edge AI Core takes |
| `meta.json` | where the export came from, as [meta.quantize.schema.json](../../common/schemas/meta.quantize.schema.json) describes |

## Where the quantization ranges come from

The quantization follows what [ST Edge AI Core recommends](https://stedgeai-dc.st.com/assets/embedded-docs/quantization.html).
It uses the QDQ format with per-channel int8 weights and int8 activations, and takes
the activation ranges by MinMax.

The rows those ranges are measured on are the train rows the models were fitted on.
The quantizer reads those rows in batches, `BATCH` rows or a few more each. `BATCH`
is the batch the autoencoders were fitted at, but
[fit](../../models/docs/fit.md) reads its own from the `--models` file. Quantize
stops when the two differ, so `BATCH` cannot stand for a value the run never used.

## Versions

ONNX 1.16.2 and ONNX Runtime 1.19.2, the ones ST Edge AI Core 4.0.1 bundles. ONNX
Runtime 1.19.2 is also the last version that installs on Python 3.9.
