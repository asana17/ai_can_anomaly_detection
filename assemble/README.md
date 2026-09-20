# assemble

Builds the train and test sets from the preprocess pipeline, split by time.

Documented under [docs/](docs).

- [grid](docs/grid.md) reads logs into one row per tick and uploads them, and sets the
  period, max hold, segment rule and dtypes that attack_set follows too.
- [scale](docs/scale.md) fits the mean and std from the rows given, and puts rows on
  them.
- [split](docs/split.md) counts each log's seconds above the minimum speed on the grid,
  cuts the logs into train and test by time on them, and uploads the cut.
- [train_set](docs/train_set.md) cuts the training rows into train and calibration.
- [injected_frames](docs/injected_frames.md) writes the attacked test logs frame by
  frame, as Parquet.
- [attack_set](docs/attack_set.md) builds the test arrays with attacks in them, and
  says which rows each one changed.
- [dataset](docs/dataset.md) runs all of these over the logs and writes the result
  into `out`.

## Tests

Run from the repository root.

```
python3 -m pytest
```
