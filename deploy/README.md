# deploy

Turns the models from [models](../models) into the files a board can run.

Documented under [docs/](docs).

- [export](docs/export.md) writes every nonlinear autoencoder of a fit out as float
  ONNX.
- [quantize](docs/quantize.md) quantizes the float files of an export to int8, with the
  threshold each int8 file scores the calibration rows at. It is run only when an int8
  model is wanted.
- [generate](docs/generate.md) generates C code with ST Edge AI Core from every float
  file of an export.

What the int8 files cost in detection is measured by
[evaluate.quantize.compare](../evaluate/docs/quantize_compare.md), and what it came to
is in [results](results.md).
