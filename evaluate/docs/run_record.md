# run record

`runs_clone` is a clone of [asana17/ai_can_anomaly_detection_runs](https://github.com/asana17/ai_can_anomaly_detection_runs). Each run adds `results/<start time>/`
to it, then commits and pushes that directory. A run never writes into an existing
directory, so earlier runs stay as they were.

| file | holds |
|---|---|
| `weights.safetensors` | every fitted model of the run |
| `meta.json` | what the weights alone cannot reproduce |

In `weights.safetensors` a tensor's name says which model it belongs to. PCA's are
`pca.k{k}.centre` and `pca.k{k}.basis`. An autoencoder's are its `state_dict` names
under `linear_ae.k{k}.` or `nonlinear_ae.h{h}.k{k}.`.

| key in `meta.json` | holds |
|---|---|
| `commit` | the commit of this repository the run started from |
| `uncommitted` | `git status --porcelain` at the start, empty when nothing was changed |
| `seeds` | `SEED` and `TORCH_SEED` |
| `hyperparameters` | the other values set at the top of `run.py`, and how many logs were read |
| `metrics` | the hours scored, the attacks scored, and each row of both tables |
| `versions` | Python, NumPy, torch and the platform |
| `started`, `finished`, `seconds` | when the run started and ended, and how long it took |
