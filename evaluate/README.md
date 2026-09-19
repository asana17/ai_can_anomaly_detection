# evaluate

Runs the whole comparison over a set of logs. It compares these detectors.

- the instant rules alone, which read physical values
- the instant rules together with PCA, once for each component count
- the instant rules together with a linear autoencoder, once for each component count
- the instant rules together with a nonlinear autoencoder, once for each component
  count and each `HIDDEN`

The models are there to catch what the rules miss, so each is compared with the rules
alone. The component count `k` is how many numbers a row is compressed into. PCA keeps
`k` components, and each autoencoder gets the same `k` as `latent_dim`, so all of them
are compared at the same `k`. The linear and nonlinear autoencoders differ only in the
hidden layer and its ReLU, so the gap between them is what the nonlinearity buys.

```
python3 -m evaluate.pc.run out runs_clone
```

`out` is the dataset [assemble.dataset](../assemble/docs/dataset.md) built. The run
reads the rows and the attacks from it, then asks the rules and each model for one flag
per row. The runs of flags, the counting and the table are
the same for all of them.

Documented under [docs/](docs).

- [pc_run](docs/pc_run.md) says what is reused, what counts as an alarm, and how each
  parameter was set.
- [run_record](docs/run_record.md) says what each run keeps.
- [quantize_compare](docs/quantize_compare.md) says how the cost of quantizing a model
  to int8 is measured.

## Tests

Run from the repository root.

```
python3 -m pytest
```
