# export

The board runs C code that ST Edge AI Core generates from an ONNX file. `export` takes
one nonlinear autoencoder a run of `evaluate.pc.run` fitted, writes it out as float and
int8 ONNX for that, and keeps both in the runs repository.

## Running it

```
python3 -u -m board.export "data/part_*/*.csv" out runs_clone started k h
```

| argument | what it is |
|---|---|
| `"data/part_*/*.csv"` | the logs the run read |
| `out` | the cache `evaluate.pc.run` keeps |
| `runs_clone` | a clone of the [runs repository](../../evaluate/docs/run_record.md), the same one `evaluate.pc.run` takes |
| `started` | the run's `<start time>` under `results/`, such as `20260915-223031` |
| `k`, `h` | which of the run's nonlinear autoencoders, by `latent_dim` and hidden units |

## What it writes

Each export adds `board/<export time>/` to `runs_clone`, then commits and pushes that
directory. It never writes into an existing directory, and never into the run's.

| file | holds |
|---|---|
| `nonlinear_ae_k{k}_h{h}_float.onnx` | the model in float32 |
| `nonlinear_ae_k{k}_h{h}_int8.onnx` | the model in int8 QDQ form, the input ST Edge AI Core takes |
| `meta.json` | what the two files alone cannot say |

The ONNX files hold only the model's forward pass. The mean squared error is taken
outside it, from the input row and the reconstruction. The quantizer's preprocessed
model is only a step on the way, so it is not kept.

| key in `meta.json` | holds |
|---|---|
| `run` | the run the weights came from, as `results/<start time>` |
| `k`, `h` | which of its nonlinear autoencoders |
| `commit` | the commit of this repository the export ran from |
| `uncommitted` | `git status --porcelain` at the start, empty when nothing was changed |
| `versions` | Python, NumPy, torch, ONNX and ONNX Runtime |
| `exported` | when the export started |

## Where the model comes from

The weights are read from the run's `weights.safetensors`. Nothing is fitted here, so
the ONNX files hold exactly the model the run reported on. A `k` and `h` the run did
not fit stops the export before anything is written.

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
