# fit

`fit` reads a [train set](../../assemble/docs/train_set.md) and takes its training
rows. It fits every model listed in a JSON file. It then uploads the fitted models, as
a directory of the runs repository, `models/<time>/`.

`fit` reads no attacked row. Thresholds are [calibrate](calibrate.md)'s.

## Running it

```
python3 -m models.fit repo revision train_sets/<time> local_dir runs_repo runs_dir [--models models.json] [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `train_sets/<time>/` |
| `revision` | commit of `repo` to read it at, as [train_set](../../assemble/docs/train_set.md) printed it |
| `train_sets/<time>` | the train set whose rows the models are fitted on. The log split and grid it names are read too |
| `local_dir` | local folder the dataset directories are downloaded to |
| `runs_repo` | Hugging Face model repo the run is uploaded to, needs `hf auth login` |
| `runs_dir` | local folder `models/<time>/` is written to, kept after the upload |
| `--models` | JSON file listing the models to fit. Without it, `models/models.json`, the list this repository's runs use |
| `--rebuild` | fit again even if `runs_repo` already holds a run with the same `inputs` |

It writes these files into `runs_dir/models/<time>/` and uploads that directory to
`runs_repo` as `models/<time>/`. The directory is claimed before the first model is
fitted, so a login that does not work stops the command at the start rather than after
hours of training.

| file | holds |
|---|---|
| `weights.safetensors` | every fitted model's weights, and `scale.mean` and `scale.std`, the values its rows were z-scored with |
| `losses.json` | one entry per autoencoder, the model and its mean training loss for each epoch it ran, as [losses.schema.json](../../common/schemas/losses.schema.json) describes |
| `meta.json` | what was fitted, and on what, as [meta.models.schema.json](../../common/schemas/meta.models.schema.json) describes |

A tensor carries the name of the model it belongs to, `pca.k{k}.centre` and
`pca.k{k}.basis` for PCA, an autoencoder's own `state_dict` names under
`linear_ae.k{k}.` or `nonlinear_ae.h{h}.k{k}.`.

## The rows it fits on

`fit` reads the train rows and drops none of them. The
[train set](../../assemble/docs/train_set.md) already chose them, the rows above
`MIN_SPEED`.

`MIN_SPEED` is the value the [log split](../../assemble/docs/split_test_logs.md) was cut
with. It comes from the log split's `meta.json`, and `fit` records it in its own.

## The scale

`scale_for(rows)` takes the mean and std of a [scale](../../preprocess/docs/scale.md)
from the train rows, and the models are fitted on the rows z-scored with it. A signal
that never changes keeps a std of 1, so it stays at 0 instead of dividing by zero. The
scale goes into `weights.safetensors`, and whatever scores rows for these models reads
it from there.

The mean and std are taken only over the train rows, the moving rows, because those
are the rows the models are fitted on and asked about. Stopped rows spread some
signals far wider than moving ones do, such as `clutch_slip` and `input_shaft_speed`.
With them in the std, those signals would count for less in the residual than the
others.

## The models it fits

`fit` fits the models the `--models` file lists. That file is a JSON list, one entry
per model, naming the model and the values it is fitted with. A value written as a
list expands to one model per value, so a single entry asks for a sweep.

```json
[{"model": "pca", "k": [2, 4]},
 {"model": "nonlinear ae", "k": [2, 4], "hidden": [32, 64], "epochs": 1000,
  "batch": 1024, "rate": 0.001, "improvement": 0.0001, "patience": 10, "seed": 3}]
```

That asks for six models, PCA at `k` 2 and 4, and a nonlinear autoencoder at each of
the four pairs of `k` and `hidden`. PCA is solved rather than trained, so it takes
none of the values below `hidden`.

`inputs` records the models after the lists are spread out, one entry each, so the run
says what every model was fitted with.

## The models this repository fits

`models/models.json` asks for three models, a nonlinear autoencoder with `hidden` 128
at `k` 4, 8 and 12. The set was chosen without looking at any attack.

- No PCA and no linear autoencoder. They were the linear baselines of the instant
  pair, which is finished, as [results](../../evaluate/results.md) reports. Trained on
  squared error, the linear autoencoder learns the same subspace as PCA (Baldi and
  Hornik, 1989).
- `hidden` 128 only. The board runs the heaviest model, and that one also shows its
  load best.
- `k` 4, 8 and 12 compress the 17 signals in even steps of 4. At `k` 2 the model does
  not rebuild normal rows well. Its threshold from the normal calibration rows was
  about 4 times that at `k` 4, 2.25 against 0.54 for `hidden` 128 in run 1. At `k` 16
  only one dimension is dropped, so a row can pass through almost unchanged.

Earlier runs fitted 40 models. Their `models.json` still lists PCA and the linear
autoencoder, so `fit` and the schema keep them.

## The autoencoder values

How each value an autoencoder is fitted with was set. None of them was chosen by
looking at the test set.

| name | value | how it was set |
|---|---|---|
| `epochs` | 1000 | a cap. The report shows how many epochs each fit ran, and fewer than 1000 means it stopped on its own. Raised from 500, where 8 of the 24 nonlinear fits were cut off, on whether fits stop on their own and never on detection. |
| `batch` | 1024 | from 1024 and 4096, on how close the linear autoencoder's training loss came to PCA's and how long it took. No attack was used. The nonlinear autoencoder uses the same value. |
| `rate` | 1e-3 | Adam's default in PyTorch |
| `improvement` | 1e-4 | the default `threshold` of PyTorch's `ReduceLROnPlateau` |
| `patience` | 10 | the default `patience` of the same |
| `seed` | set per run | the torch rng an autoencoder is built and trained with. It is changed between runs to show how far it moves the numbers, as [results](../../evaluate/results.md) reports. |
| `hidden` | 128 | a stated choice, as [above](#the-models-this-repository-fits). It is at least `signals`, so `latent_dim` stays the narrowest layer at every `k`. Earlier runs also fitted 32 and 64. |

`batch` was compared at every `k`. Up to `k` 14 the two sizes came within 0.3% of each
other and within 0.8% of PCA, and 1024 took less time at every `k`. At `k` 16 1024
came within 13% and 4096 within 98%.
