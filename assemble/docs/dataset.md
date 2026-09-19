# dataset

Builds the grid of the training logs, which the train and calibration rows are cut
from, and the attacked test rows, and writes them into `out`.
Putting the logs on the grid and building the attack set take long, so each is written
once and read back from `out` after that.

```
python3 -m assemble.dataset "data/part_*/*.csv" out
```

It measures each log's seconds above `MIN_SPEED`, [splits](split.md) the logs, puts the
training logs on the [grid](train_set.md), and builds the [attack set](attack_set.md)
on the scale fitted to them. A step whose logs and settings match what is in `out`
already is not run again.

| file | holds |
|---|---|
| `seconds.json` | each log's seconds above `MIN_SPEED`, kept for every log ever measured |
| `grid.json` | the training logs and the grid settings the grid was built with |
| `grid_raw.npy`, `grid_t.npy`, `grid_seg.npy` | the training logs on the grid |
| `built.json` | the logs and the settings the attack set was built with |
| `attacked.json` | where each attack sits and how far it moved the rows |
| `attacked_{rows,raw,t,seg,label,wheel}.npy` | the test logs with the attacks in, on the grid |
