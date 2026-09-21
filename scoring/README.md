# scoring

Scores a set of rows. [preprocess](../preprocess) marks the moving rows,
[rules](../rules) flag the ones they hit, and every model of a fit scores them.
[detect](../detect) turns the scores and the flags into alarms.

```
python3 -m scoring.score REPO REVISION SET LOCAL_DIR RUNS_REPO REVISION MODELS RUNS_DIR
```

Documented under [docs/](docs).

- [score](docs/score.md) scores each row of a set with every model, and marks the rows
  a rule hits. [calibrate](../models/docs/calibrate.md) and
  [run_test_set](../evaluate/docs/run_test_set.md) run it.

## Tests

Run from the repository root.

```
python3 -m pytest
```
