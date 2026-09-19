# export

The board runs C code that ST Edge AI Core generates from an ONNX file. `export` takes
every nonlinear autoencoder a run of `evaluate.pc.run` fitted, writes each one out as
float and int8 ONNX for that, and keeps them in the runs repository.

## Running it

```
python3 -u -m quantize.export repo revision out runs_clone started
```

| argument | what it is |
|---|---|
| `repo`, `revision` | the Hugging Face dataset the run read, as its `meta.json` names it under `dataset` |
| `out` | where that dataset is fetched to |
| `runs_clone` | a clone of the [runs repository](../../evaluate/docs/run_record.md), the same one `evaluate.pc.run` takes |
| `started` | the run's `<start time>` under `results/`, such as `20260915-223031` |

Which autoencoders are written is not an argument. The run's `weights.safetensors` says
which `k` and `h` it fitted, and all of them are written.

## What it writes

Each export adds `quantize/<export time>/` to `runs_clone`, then commits and pushes that
directory. It never writes into an existing directory, and never into the run's.

| file | holds |
|---|---|
| `nonlinear_ae_k{k}_h{h}_float.onnx` | one autoencoder in float32 |
| `nonlinear_ae_k{k}_h{h}_int8.onnx` | the same one in int8 QDQ form, the input ST Edge AI Core takes |
| `meta.json` | what the ONNX files alone cannot say |

The two ONNX files are written for every `k` and `h`, so one directory holds the whole
run and one call is one commit.

The ONNX files hold only the model's forward pass. The mean squared error is taken
outside it, from the input row and the reconstruction. The quantizer's preprocessed
model is only a step on the way, so it is not kept.

| key in `meta.json` | holds |
|---|---|
| `run` | the run the weights came from, as `results/<start time>` |
| `dataset` | the Hugging Face dataset the calibration rows came from, its `repo` and the full commit of its `revision` |
| `models` | the `k` and `h` of every autoencoder in the directory, each with the `int8_threshold` its int8 file scores the run's calibration rows at, at `TARGET` |
| `commit` | the commit of this repository the export ran from |
| `uncommitted` | `git status --porcelain` at the start, empty when nothing was changed |
| `versions` | Python, NumPy, torch, ONNX and ONNX Runtime |
| `exported` | when the export started |

## Where the model comes from

The weights are read from the run's `weights.safetensors`. Nothing is fitted here, so
the ONNX files hold exactly the models the run reported on.

## Where the quantization ranges come from

The quantization follows what [ST Edge AI Core recommends](https://stedgeai-dc.st.com/assets/embedded-docs/quantization.html).
It uses the QDQ format with per-channel int8 weights and int8 activations, and takes
the activation ranges by MinMax.

The ranges come from the same training rows the run fitted on, built from the logs.
`out` only saves building those rows again, so `export` also works without it. The rows
match the run's only when the code builds them the way it did at the run's `commit`.
The int8 file therefore cannot be rebuilt from the weights alone, which is why it is
kept.

## Versions

ONNX 1.16.2 and ONNX Runtime 1.19.2, the ones ST Edge AI Core 4.0.1 bundles. ONNX
Runtime 1.19.2 is also the last version that installs on Python 3.9.
