# run record

`runs_repo` is a Hugging Face model repository, such as
[asana17/ai_can_anomaly_detection_runs](https://huggingface.co/asana17/ai_can_anomaly_detection_runs).
`runs_dir` is a local directory laid out like it.

When a run starts, it checks that `hf auth login` works and that `results/<start time>/`
is in neither place, then makes that directory in `runs_dir`. At the end it writes the
files there and uploads the directory in one commit. If the upload fails, the files stay
in `runs_dir` and the run prints the `hf upload` command that uploads them later.

| file | holds |
|---|---|
| `weights.safetensors` | every fitted model of the run |
| `meta.json` | what the weights alone cannot reproduce |

In `weights.safetensors` a tensor's name says which model it belongs to. PCA's are
`pca.k{k}.centre` and `pca.k{k}.basis`. An autoencoder's are its `state_dict` names
under `linear_ae.k{k}.` or `nonlinear_ae.h{h}.k{k}.`. `scale.mean` and `scale.std`
are the z-score every model's rows are put on.

| key in `meta.json` | holds |
|---|---|
| `commit` | the commit of this repository the run started from |
| `uncommitted` | `git status --porcelain` at the start, empty when nothing was changed |
| `dataset` | the Hugging Face dataset the run read, its `repo` and the full commit of its `revision` |
| `seeds` | `SEED` and `TORCH_SEED` |
| `hyperparameters` | the other values in `common/settings.py`, and how many logs were read |
| `metrics` | the hours scored, the attacks scored, and each row of both tables |
| `versions` | Python, NumPy, torch and the platform |
| `started`, `finished`, `seconds` | when the run started and ended, and how long it took |
