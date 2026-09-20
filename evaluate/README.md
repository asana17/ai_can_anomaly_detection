# evaluate

Turns the rows [assemble](../assemble) built into detectors, and measures what they
catch.

A detector is the instant rules, or the rules together with one model. The models are
there to catch what the rules miss, so each one is compared with the rules alone. The
component count `k` is how many numbers a row is compressed into. PCA keeps `k`
components, and each autoencoder gets the same `k` as its `latent_dim`, so every model
is compared at the same `k`. The linear and nonlinear autoencoders differ only in the
hidden layer and its ReLU, so the gap between them is what the nonlinearity buys.

Building a detector takes two commands, each writing one directory of the runs
repository.

```
python3 -m evaluate.fit REPO REVISION TRAIN_SET LOCAL_DIR RUNS_REPO RUNS_DIR
python3 -m evaluate.calibrate RUNS_REPO REVISION RUN RUNS_DIR LOCAL_DIR
```

Scoring the attacked test rows is still `evaluate.pc.run`, which fits, thresholds and
scores in one command and reads the dataset in the old flat layout.

Documented under [docs/](docs).

- [fit](docs/fit.md) trains the models on the train rows and uploads them.
- [calibrate](docs/calibrate.md) gives each model the score above which a row counts
  as an anomaly.
- [pc_run](docs/pc_run.md) says what is reused, what counts as an alarm, and how each
  parameter was set.
- [quantize_compare](docs/quantize_compare.md) says how the cost of quantizing a model
  to int8 is measured.

## Tests

Run from the repository root.

```
python3 -m pytest
```
