# quantize

Turns the models from [models](../models) into the files a board can run.

Documented under [docs/](docs).

- [export](docs/export.md) writes every nonlinear autoencoder of a run of
  `evaluate.pc.run` out as float and int8 ONNX, with the threshold the int8 file scores
  the calibration rows at.

What the int8 files cost in detection is measured by
[evaluate.quantize.compare](../evaluate/docs/quantize_compare.md), and what it came to
is in [results](results.md).
