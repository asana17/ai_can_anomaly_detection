# export

The board runs C code that ST Edge AI Core generates from an ONNX file. `export` takes
one nonlinear autoencoder a run of `evaluate.pc.run` fitted, and writes it out as float
and int8 ONNX for that.

## Running it

```
python3 -u -m board.export "data/part_*/*.csv" out run_dir k h dest
```

| argument | what it is |
|---|---|
| `"data/part_*/*.csv"` | the logs the run read |
| `out` | the cache `evaluate.pc.run` keeps |
| `run_dir` | one `results/<start time>/` directory a run added to the [runs repository](../../evaluate/docs/run_record.md) |
| `k`, `h` | which of the run's nonlinear autoencoders, by `latent_dim` and hidden units |
| `dest` | where the ONNX files go |

## What it writes

| file | holds |
|---|---|
| `nonlinear_ae_k{k}_h{h}_float.onnx` | the model in float32 |
| `nonlinear_ae_k{k}_h{h}_prepared.onnx` | the float model after the quantizer's preprocessing |
| `nonlinear_ae_k{k}_h{h}_int8.onnx` | the model in int8 QDQ form, the input ST Edge AI Core takes |

The ONNX files hold only the model's forward pass. The mean squared error is taken
outside it, from the input row and the reconstruction.

## Where the model comes from

The weights are read from the `weights.safetensors` in `run_dir`. Nothing is fitted
here, so the ONNX files hold exactly the model the run reported on.

## Where the quantization ranges come from

The quantization follows what [ST Edge AI Core recommends](https://stedgeai-dc.st.com/assets/embedded-docs/quantization.html).
It uses the QDQ format with per-channel int8 weights and int8 activations, and takes
the activation ranges by MinMax.

The ranges come from the same training rows the run fitted on, built from the logs.
`out` only saves building those rows again, so `export` also works without it. The rows
match the run's only when the code builds them the way it did at the run's `commit`.

## Versions

ONNX 1.16.2 and ONNX Runtime 1.19.2, the ones ST Edge AI Core 4.0.1 bundles. ONNX
Runtime 1.19.2 is also the last version that installs on Python 3.9.
