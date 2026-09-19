# quantize compare

Measures what quantizing a model to int8 costs.

```
python3 -m evaluate.quantize.compare repo revision out runs_repo runs_dir exported...
```

| argument | what it is |
|---|---|
| `repo`, `revision` | the Hugging Face dataset the run was fitted on, as the run's `meta.json` names it under `dataset` |
| `out` | where that dataset is fetched to |
| `runs_repo`, `runs_dir` | the [runs repository](run_record.md) and its local copy |
| `exported` | one or more `<export time>` under `quantize/`, such as `20260916-221145` |

Each export's directory is downloaded into `runs_dir`. Its `meta.json` names the run and
every `k` and `h` it holds, and the run's directory is downloaded too. Each `k` and `h`
is measured.

[pc run](pc_run.md) fits the models. [export](../../quantize/docs/export.md) quantizes a
copy of each nonlinear autoencoder to int8. `compare` then puts a model and its int8
ONNX through the same two steps.

1. The model takes a threshold from the run's calibration rows at `TARGET`. The int8
   ONNX takes a threshold the same way, from the scores the int8 ONNX gives those rows.
2. The model scores the run's attacked test rows, and so does the int8 ONNX, with the
   run's rules, `HOLD` and counting.

The arithmetic that scores a row is the only difference between the model and the int8
ONNX, so the gap between the two rows of the table is what the quantization costs.

Note: export generates a float ONNX and then converts it to an int8 ONNX. Since the
float ONNX holds the same arithmetic as the torch model, it is not compared here.
