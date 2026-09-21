# assemble

Builds the train and test sets from the preprocess pipeline, split by time.

Documented under [docs/](docs).

- [grid](docs/grid.md) reads logs into one row per tick and uploads them, and sets the
  period, max hold, segment rule and dtypes that test_set follows too.
- [split_test_logs](docs/split_test_logs.md) counts each log's seconds above the
  minimum speed on the grid, cuts the logs into test and non-test by time on them, and
  uploads the cut.
- [calibration_set](docs/calibration_set.md) cuts the non-test logs' time into
  calibration blocks and picks the rows a threshold is taken from.
- [train_set](docs/train_set.md) picks the rows a model is fitted on, away from the
  calibration blocks.
- [injected_frames](docs/injected_frames.md) writes the attacked test logs frame by
  frame, as Parquet.
- [test_set](docs/test_set.md) builds the test arrays with attacks in them, and
  says which rows each one changed.

## Tests

Run from the repository root.

```
python3 -m pytest
```
