# evaluate

Turns the rows [assemble](../assemble) built into detectors, and measures what they
catch.

A detector is the instant rules, or the rules together with one model. The models are
there to catch what the rules miss, so each one is compared with the rules alone. The
component count `k` is how many numbers a row is compressed into. PCA keeps `k`
components, and each autoencoder gets the same `k` as its `latent_dim`, so every model
is compared at the same `k`. The linear and nonlinear autoencoders differ only in the
hidden layer and its ReLU, so the gap between them is what the nonlinearity buys.

Building a detector and measuring it is one command per stage, each writing one
directory of the runs repository.

```
python3 -m evaluate.fit REPO REVISION TRAIN_SET LOCAL_DIR RUNS_REPO RUNS_DIR
python3 -m evaluate.calibrate RUNS_REPO REVISION MODELS RUNS_DIR LOCAL_DIR
python3 -m evaluate.pc.score REPO REVISION ATTACK_SET LOCAL_DIR RUNS_REPO REVISION THRESHOLDS RUNS_DIR
```

Documented under [docs/](docs).

- [fit](docs/fit.md) trains the models on the train rows and uploads them.
- [calibrate](docs/calibrate.md) gives each model the score above which a row counts
  as an anomaly.
- [pc_score](docs/pc_score.md) counts what each detector catches on the attacked test
  rows.
- [pc_run](docs/pc_run.md) says what counts as an alarm, and how each parameter was
  set.

## Tests

Run from the repository root.

```
python3 -m pytest
```
