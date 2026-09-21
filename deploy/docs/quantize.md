# quantize

`quantize` takes every float file of one [export](export.md), quantizes it to int8,
and keeps them in the runs repository. It is run only when an int8 model is wanted.

## Running it

```
python3 -u -m deploy.quantize runs_repo revision onnx/<time> runs_dir local_dir [--rebuild]
```

| argument | what it is |
|---|---|
| `runs_repo` | Hugging Face model repo holding the export and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the export at, as [export](export.md) printed it |
| `onnx/<time>` | the export to quantize |
| `runs_dir` | local folder the export is downloaded to and `quantize/<time>/` is written to |
| `local_dir` | local folder the train set the models name is downloaded to |
| `--rebuild` | quantize again even if `runs_repo` already holds a directory with the same `inputs` |

## What it writes

It writes these files into `runs_dir/quantize/<time>/` and uploads that directory to
`runs_repo` as `quantize/<time>/`.

| file | holds |
|---|---|
| `nonlinear_ae_k{k}_h{h}_int8.onnx` | one file per model, in int8 QDQ form, the input ST Edge AI Core takes |
| `meta.json` | where the export came from, and the threshold each int8 file reaches |

| key in `meta.json` | holds |
|---|---|
| `inputs` | the export, `TARGET` and `BATCH`. A later call with the same `inputs` reuses this directory |
| `onnx` | the export the float files came from, as a repo, a revision and a path |
| `models`, `train_set`, `split`, `grid` | the directories the export records |
| `thresholds` | one entry per model, the model as the models directory writes it down, and the `int8_threshold` its int8 file reaches on the calibration rows at `TARGET` |
| `versions` | Python, NumPy, ONNX and ONNX Runtime |
| `commit`, `uncommitted` | the commit of this repository it ran from, and any uncommitted files |
| `started`, `finished` | when it started and ended |

## Where the int8 thresholds come from

An int8 model does not score a row quite as the float model does, so it cannot keep
the float model's threshold. Each int8 file scores the calibration rows of the train
set, and its threshold is the score `TARGET` of them are above, as
[calibrate](../../evaluate/docs/calibrate.md) does for the float models.

## Where the quantization ranges come from

The quantization follows what [ST Edge AI Core recommends](https://stedgeai-dc.st.com/assets/embedded-docs/quantization.html).
It uses the QDQ format with per-channel int8 weights and int8 activations, and takes
the activation ranges by MinMax.

The rows those ranges are measured on are the train rows the models were fitted on.

## Versions

ONNX 1.16.2 and ONNX Runtime 1.19.2, the ones ST Edge AI Core 4.0.1 bundles. ONNX
Runtime 1.19.2 is also the last version that installs on Python 3.9.
