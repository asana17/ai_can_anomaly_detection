# board compare

Measures what quantizing a model to int8 costs.

```
python3 -m evaluate.board.compare "data/part_*/*.csv" out runs_clone exported...
```

`exported` is a directory under `board/` in the runs repository, such as
`20260916-082021`. The `meta.json` in that directory names the run, `k` and `h`.

[pc run](pc_run.md) trains one model. [export](../../board/docs/export.md) quantizes a
copy of that model to int8. `compare` then puts the model and the int8 ONNX through the
same two steps.

1. The model takes a threshold from the run's calibration rows at `TARGET`. The int8
   ONNX takes a threshold the same way, from the scores the int8 ONNX gives those rows.
2. The model scores the run's attacked test rows, and so does the int8 ONNX, with the
   run's rules, `HOLD` and counting.

The arithmetic that scores a row is the only difference between the model and the int8
ONNX, so the gap between the two rows of the table is what the quantization costs.

The rows come from `out`, the cache the run read.

Note: export generates a float ONNX and then converts it to an int8 ONNX. Since the
float ONNX holds the same arithmetic as the torch model, it is not compared here.
