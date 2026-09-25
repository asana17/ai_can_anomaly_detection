# CAN anomaly detection

Detects unknown anomalies on a heavy duty truck's CAN bus (J1939/FMS), meant to run
on a small microcontroller (NUCLEO-H533RE).

Deterministic rules catch what can be written as an invariant, a value out of range
or two signals that must agree, like the engine and wheel speeds picking out the gear
the transmission reports. They are in [rules/](rules).

What no invariant covers is left to a model, a nonlinear
[autoencoder](models/docs/autoencoder.md). A model trains offline on a PC on
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
- [pipeline/](pipeline) runs every stage from the grid to the test run in one command,
  on HEAD's code in a worktree of its own, and says first what a run would build.
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
- Decide whether the matched replay is the attack the windowed pair is measured on.
  `assemble.test_set --attack matched_replay` replays a PGN from a donor that held this
  log's speed and gear over the whole stretch. Measured on 300 test logs against the fit
  of 2026-09-22, at `HOLD` 10: the rules and change_limit together catch 2 of 76 against
  39 of 86 plain replays, and the nonlinear autoencoder k=8 takes that to 15 of 76
  against 64 of 86. A PCA over ten rows, fitted for the measurement alone, adds 9 of 76,
  but it reads only 48 of 86 plain replays, so it says nothing about what a window is
  worth yet. What no detector reads is a matched replay of TCO1, ETC1 or VDC2, whose
  values the matched speed and gear already fix or which no other PGN reads. The numbers
  are in [attack/measurements.md](attack/measurements.md).
- Then widen to a stretch of time, VAR against a windowed autoencoder. It is what the
  new attack is built against. The window model is an aid to alarm A, the rules and the
  instant model on every tick. On the board it runs in a lower priority task, late and
  skipping windows when time is short. It is judged by what it adds over alarm A and how
  many rows later. Its floor is the instant rules OR the instant model, flagged on k of
  the window's W rows. Report what it adds in catches and in false alarms. Also compare
  it with the instant model's threshold lowered to the same false alarms. Report W at
  several values. The four items below come first.
  - On the board, put the rows in one ring in place of the row queue. preprocess writes
    it, and scoring and detect and a window scoring task read it under one mutex. Row
    flags go in an array beside it. Window scoring only copies windows for now. W and S
    belong in the window model's config header.
  - Raise an alarm when k of the last N rows are flagged, in place of `HOLD` rows in a
    row. One row that looks normal then no longer restarts the count. Report N and k at
    several values, with alarms per hour on normal data.
  - Fit and threshold each model on every normal row, rule hits included. The rules and
    the model meet in `detect` alone. `train_set` and `calibrate` still drop rule hits.
    The finished runs stay as a record.
  - Send alarms to CAN and record them to Flash, in two tasks, alarm A before B. UART
    output masks interrupts while it waits on each character.
- Add Isolation Forest beside the autoencoders, as a baseline that does not
  reconstruct.
- Rules that read the past go into alarm A. change_limit runs on rows and in C. Wire it
  into scoring and detect once the ring is in.
- Give gear_ratio and speed_agreement the row before, as change_limit has. On the
  moving grid rows of every log gear_ratio fires 317 times, most just after a shift
  while the engine still turns at the old gear's ratio. Waiting 2 s after the reported
  gear changes leaves 77. speed_agreement fires 587 times, at a median of 12 km/h/s
  against 1.0 for all moving rows, and 91 remain below 5 km/h/s. Both catch attacks no
  other rule does, so measure what each change loses on the test set.
- engine_load against actual_engine_torque over ten rows was kept from six window rules
  by how many matched replays it caught. Decide it again on normal data alone.
- A script that compares scores.

## Tests

Run from the repository root.

```
python3 -m pytest
```
