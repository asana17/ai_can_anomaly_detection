# fit

Fits the models on the train rows of a [train set](../../assemble/docs/train_set.md).
Every fitted model goes into one directory, `results/<time>/` of the runs repository.
The thresholds are [calibrate](calibrate.md)'s.

## Running it

```
python3 -m evaluate.fit repo revision train_sets/<time> local_dir runs_repo runs_dir [--models models.json] [--rebuild]
```

| argument | |
|---|---|
| `repo`, `revision` | the Hugging Face dataset repository holding `train_sets/<time>/`, and the commit to read it at |
| `train_sets/<time>` | the train set whose rows the models are fitted on. Its split and grid are read as well |
| `local_dir` | where those directories are downloaded to |
| `runs_repo`, `runs_dir` | the runs repository, and a local directory laid out like it |
| `--models` | a JSON file naming the models to fit. Without it, `evaluate/models.json`, the list this repository's runs use |
| `--rebuild` | fit again even when `runs_repo` holds a run with the same `inputs` |

## The rows

The models are fitted on the train set's train rows whose wheel speed is above
`MIN_SPEED`. That is the speed a row has to exceed to be scored, and it comes from the
[split](../../assemble/docs/split.md).

Each row is z-scored first, with the mean and std the train set saved in `scale.npy`.
[scale](../../assemble/docs/scale.md) says why.

The calibration rows and the test rows are not read here.

## The models

The file lists what to fit. A value written as a list means one model for each value
in it, so one line asks for a whole sweep.

```json
[{"model": "pca", "k": [2, 4]},
 {"model": "nonlinear ae", "k": [2, 4], "hidden": [32, 64], "epochs": 1000,
  "batch": 1024, "rate": 0.001, "improvement": 0.0001, "patience": 10, "seed": 3}]
```

## What it writes

`common/hub_dirs.reuse_or_make` makes `results/<time>/` before the first model is
fitted, writes these files into it, and uploads it in one commit.

| file | holds |
|---|---|
| `weights.safetensors` | the weights of every fitted model, and the mean and std their rows were put on |
| `losses.json` | one entry per autoencoder, the model and its mean loss on the train rows each epoch. As many losses as `epochs` means training stopped at the cap rather than on its own |
| `meta.json` | everything else the run has to record |

A tensor carries the name of the model it belongs to: `pca.k{k}.centre` and
`pca.k{k}.basis` for PCA, an autoencoder's own `state_dict` names under
`linear_ae.k{k}.` or `nonlinear_ae.h{h}.k{k}.`. `scale.mean` and `scale.std` are the
z-score.

| key in `meta.json` | holds |
|---|---|
| `inputs` | the train set, and one line per model with the values it was fitted with |
| `train_set`, `split`, `grid` | where the rows came from, each a repository, a commit and a path |
| `min_speed` | the speed a row had to exceed to be fitted on |
| `rows` | how many rows the models were fitted on |
| `versions` | Python, NumPy, torch and the platform |
| `commit`, `uncommitted` | the commit it ran from, and `git status --porcelain` there |
| `started`, `finished` | when it started and ended |
