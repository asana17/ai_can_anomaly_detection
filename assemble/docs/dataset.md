# dataset

Builds the dataset from the logs and uploads it to Hugging Face. The dataset is the
training logs on the grid, which the train and calibration rows are cut from, the scale,
and the attacked test rows.

## Running it

```
python3 -m assemble.dataset "data/part_*/*.csv" out repo branch
```

The call ends by uploading to `repo`, so log in first with `hf auth login`, using a
token that can write to it.

| argument | what it is |
|---|---|
| `out` | where the files are written, and read back on a later call |
| `repo` | the Hugging Face dataset they are uploaded to |
| `branch` | the branch of `repo` they go to, made if it is not there |

When the upload is done it prints `revision <commit hash>`. That commit of `repo` holds
exactly the files this call wrote. If the upload fails, the files stay in `out`, and it
prints the `hf upload` command that uploads them again.

## What it builds

It measures each log's seconds above `MIN_SPEED`, [splits](split.md) the logs, puts the
training logs on the [grid](train_set.md), fits the scale to their train rows, and
builds the [attack set](attack_set.md) on that scale.

Putting the logs on the grid and building the attack set take long, so a step whose
logs and settings match what `out` already holds is skipped.

## What it writes

| file | holds |
|---|---|
| `seconds.json` | `MIN_SPEED`, and each log's seconds above it, kept for every log ever measured |
| `grid.json` | the training logs and the grid settings the grid was built with |
| `grid_raw.npy`, `grid_t.npy`, `grid_seg.npy` | the training logs on the grid |
| `scale.npy` | the [scale](scale.md) fitted to the train rows, its mean then its std |
| `built.json` | the logs and the settings the attack set was built with |
| `attacked.json` | where each attack sits and how far it moved the rows |
| `attacked_{rows,raw,t,seg,label,wheel}.npy` | the test logs with the attacks in, on the grid |
