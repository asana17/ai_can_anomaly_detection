# assemble

Builds the train and test sets from the preprocess pipeline, split by time.

Documented under [docs/](docs).

- [grid](docs/grid.md) sets the period, max hold, segment rule and dtypes that
  train_set and attack_set both use.
- [scale](docs/scale.md) is the mean and std every row is z-scored by, fitted once.
- [seconds](docs/seconds.md) measures each log's seconds above the minimum speed, and
  uploads them.
- [split](docs/split.md) cuts the logs into train and test by time, sized by the
  seconds above the minimum speed in them, and the training rows into train and
  calibration.
- [train_set](docs/train_set.md) puts the training logs on the grid, and takes the mean
  and std their rows are z-scored by.
- [attack_set](docs/attack_set.md) builds the test arrays with attacks in them, and
  says which rows each one changed.
- [dataset](docs/dataset.md) runs all of these over the logs and writes the result
  into `out`.

## Tests

Run from the repository root.

```
python3 -m pytest
```
