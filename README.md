# CAN anomaly detection

Detects unknown anomalies on a heavy duty truck's CAN bus (J1939/FMS), meant to run
on a small microcontroller (NUCLEO-H533RE).

Deterministic rules catch what can be written as an invariant, a value out of range
or two signals that must agree, like the engine and wheel speeds picking out the gear
the transmission reports. They are in [rules/](rules).

What no invariant covers is left to a model, [PCA](models/docs/pca.md) or a linear or
nonlinear [autoencoder](models/docs/autoencoder.md). A model trains offline on a PC on
normal data only, then runs on the device for inference, in float since the float model
fits. Anomalies are synthesized from the normal data to test detection and never enter
training.

## Setup

Python 3.9. ONNX Runtime 1.19.2 is the last version that installs on it.

```
python3 -m pip install -r requirements.txt
```

A run reads its dataset from Hugging Face, which needs no login. Building one and
uploading it with [assemble](assemble) needs `hf auth login` with a token that can
write.

Converting a model for the board also needs [ST Edge AI Core](https://www.st.com/en/development-tools/stedgeai-core.html)
4.0.1 with its STM32 MCU component. It does not install through pip.

The logs go in `data/`, see [can_data/can_data.md](can_data/can_data.md#getting-it).

## Layout

- [can_data/](can_data) describes the logs and what profiling them found.
- [preprocess/](preprocess) turns raw CAN logs into rows, by reading the log,
  decomposing the ID, decoding signals, and putting them on a 100 ms grid.
- [assemble/](assemble) builds the grid, splits the test logs apart by time, and marks
  the calibration, train and attacked test rows, each stage a directory on the Hugging
  Face Hub.
- [attack/](attack) synthesizes anomalies for a labeled test set.
- [rules/](rules) holds the deterministic checks.
- [models/](models) holds the learned half, fits it on normal rows only, and gives
  each model the threshold a row counts as an anomaly above.
- [scoring/](scoring) scores a set of rows with every model and marks the rows a rule
  hits.
- [detect/](detect) turns the models' scores and the rule hits into alarms.
- [deploy/](deploy) writes the models out as ONNX for the NUCLEO-H533RE.
- [board/](board) holds our μT-Kernel applications for the NUCLEO-H533RE, one folder
  each. [board/docs/setup.md](board/docs/setup.md) builds and flashes one from nothing.
  [board/docs/goal.md](board/docs/goal.md) is what the board is building towards, the
  TRON Programming Contest 2026 entry, and the order it is built in.
- [common/](common) holds the settings of a run and reads and writes the Hub
  directories every stage uses. [common/docs/settings.md](common/docs/settings.md)
  says how each parameter was set. [common/schemas](common/schemas)
  describes every JSON file a stage uploads, and the tests check each file a stage
  uploads against them.
- [evaluate/](evaluate) measures what each detector catches on the attacked test rows.
  What the runs found is in [evaluate/results.md](evaluate/results.md), and what
  quantizing their models costs is in [deploy/results.md](deploy/results.md).
- `data/` holds the raw logs and is not tracked in git.

## Words

J1939's own terms, frame, PGN and SPN, are described in
[can_data/can_data.md](can_data/can_data.md). These are the ones this repo chose.

| word | what it is |
|---|---|
| log | one CSV capture, about a minute and 50,000 frames |
| signal | one decoded SPN under a name, such as `engine_speed`, 17 in all |
| row | every signal's latest value at one 100 ms tick |
| segment | a run of rows with no gap in time, broken between logs |
| residual | how far a row sits off the subspace a model fitted |
| block | one calibration window, in seconds above 5 km/h |

## TODO

- Rework `evaluate` before running `fit` and the stages after it. A row goes through
  four steps, the same on the PC and the board. The first three are the scoring
  pipeline.
  1. `preprocess` marks the moving rows.
  2. `rules` flags the moving rows it hits.
  3. The model scores the moving rows.
  4. `detect` compares the scores with the threshold, adds the rule flags, and holds
     them over `HOLD`.

  `scoring.score` runs the scoring pipeline over a set of rows and keeps each row's
  scores and rule flags. `models.calibrate` runs it over the calibration rows and takes
  the threshold from them, and `evaluate.run_test_set` runs it over the test set's rows
  and counts what each detector caught, so a new threshold or `HOLD` needs no
  rescoring. About 33 MB and 430 MB for 40 models, reckoned from the grid's row counts.
  Rows are selected by mask and never cut out, since `HOLD` counts rows in a row. No
  function joins the steps.

  The stages after it are drawn in [evaluate/README.md](evaluate/README.md).

  The same two parts run on the PC and on the board.

  | part | steps | on the PC | on the board |
  |---|---|---|---|
  | scoring pipeline | `preprocess`, `rules`, the model | `scoring.score` | in C |
  | `detect` | threshold, OR the rule flags, `HOLD` | `detect`, run by `evaluate.run_test_set` | in C |

  What still differs from today's code. `moving` and `Scale` are in `preprocess`, the
  train rows drop rule hits, the rules run over columns with numpy, and `fit` keeps the
  scale in the models, `detect` holds step 4, and `split_test_logs`, `calibration_set`,
  `train_set` and `test_set` build the sets, and `score`, `calibrate` and
  `run_test_set` are split as drawn, with their schemas and tests, and the stage docs
  follow them, and the `evaluate` box is broken up, `fit` and `calibrate` into
  `models`, `score` into `scoring`, and `run_test_set` and `count_alarms` left in
  `evaluate`, all done 2026-09-22.

- Draw the attacks over the test span's time rather than one per log. One per log puts
  four times as many per moving hour in the logs that move least. Measure first whether
  that shifts a model's numbers, from `caught` in a score. The rules catch the same
  share in every band of a log's moving seconds.
- Run `fit` and the stages after it on every log, on `train_sets/20260922-100444` and
  `test_sets/20260922-110745`. They passed on one day of logs in the smoke repos. Then
  score one other split, the first 25% of the time as test.
- Build the board application in the order of [board/docs/goal.md](board/docs/goal.md),
  due 2026-09-30. Step 3 there, the model, runs on the board and matches ONNX Runtime
  on 80 rows. Counting the calibration rows its difference moves across the threshold
  waits for `score`, and more rows wait for fetching them from the dataset. Step 4
  runs on the board. `scoring_and_detect_from_flash` scores Flash rows and raises the
  alarm, and `can_path_from_flash` replays CAN frames through the slots, a preprocess
  task on a 0.1 s cyclic handler, scoring and detect, and report. Next is the docs for
  the CAN side, how to connect the receive callback, the FDCAN interrupt priority `DI`
  must mask, and what the CAN side builds. Then steps 2, 5 and 6.
- Add kinds of anomaly beyond replay to the attacked test set, designed against the
  rules and the instant models. The instant models catch replay, so the next attack
  keeps every row inside the training distribution. A donor matched on speed and gear
  leaves only the disagreement over time.
- Then widen to a stretch of time, VAR against a windowed autoencoder. It is what the
  new attack is built against. The board wants one as well, as the best-effort layer
  under the rules and the instant model.
- Add Isolation Forest beside the autoencoders, as a baseline that does not
  reconstruct.
- Restate [can_data/measurements.md](can_data/measurements.md) over every log.
- Settle whether the rules are a floor the models build on.
- A script that compares scores.
- Rerun the linear autoencoder checks in the runs repo's `checks/` from a committed
  script, on the current dataset.

## Tests

Run from the repository root.

```
python3 -m pytest
```
