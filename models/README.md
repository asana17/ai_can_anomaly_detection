# models

The learned half of the detector. Rules state what the bus must do; these learn what
it usually does, and report what does not fit.

Fitting them and giving each one a threshold is one command per stage, each writing one
directory of the runs repository.

```
python3 -m models.fit REPO REVISION TRAIN_SET LOCAL_DIR RUNS_REPO RUNS_DIR
python3 -m models.calibrate RUNS_REPO REVISION MODELS RUNS_DIR LOCAL_DIR
```

Documented under [docs/](docs).

- [pca](docs/pca.md) scores a row by how far it sits off the subspace normal traffic
  occupies.
- [autoencoder](docs/autoencoder.md) scores a row by its reconstruction error.
- [fit](docs/fit.md) trains the models on the train rows and uploads them.
- [calibrate](docs/calibrate.md) gives each model the score above which a row counts
  as an anomaly.

Each is fit on normal rows only, from [assemble](../assemble). Attacks come from
[attack](../attack) and are never seen during fitting.

## Tests

Run from the repository root.

```
python3 -m pytest
```
