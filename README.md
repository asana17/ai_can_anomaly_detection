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
  What quantizing their models costs is in [deploy/results.md](deploy/results.md).
- [pipeline/](pipeline) runs every stage from the grid to the test run in one command,
  on HEAD's code in a worktree of its own, and says first what a run would build.
- `data/` holds the raw logs and is not tracked in git.
- [THIRD_PARTY.md](THIRD_PARTY.md) lists the software and data from others and their
  licenses.

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
  4. `detect` compares the scores with the threshold, adds the rule flags, and raises
     an alarm when k of the last N rows are flagged.

  `scoring.score` runs the scoring pipeline over a set of rows and keeps each row's
  scores and rule flags. `models.calibrate` runs it over the calibration rows and takes
  the threshold from them, and `evaluate.run_test_set` runs it over the test set's rows
  and counts what each detector caught, so a new threshold or k needs no
  rescoring. About 33 MB and 430 MB for 40 models, reckoned from the grid's row counts.
  Rows are selected by mask and never cut out, since the alarm counts rows next to each
  other. No function joins the steps.

  The stages after it are drawn in [evaluate/README.md](evaluate/README.md).

  The same two parts run on the PC and on the board.

  | part | steps | on the PC | on the board |
  |---|---|---|---|
  | scoring pipeline | `preprocess`, `rules`, the model | `scoring.score` | in C |
  | `detect` | threshold, OR the rule flags, k of the last N | `detect`, run by `evaluate.run_test_set` | in C |

  What still differs from today's code. `moving` and `Scale` are in `preprocess`, the
  rules run over columns with numpy, and `fit` keeps the scale in the models, `detect`
  holds step 4, and `split_test_logs`, `calibration_set`, `train_set` and `test_set`
  build the sets, and `score`, `calibrate` and
  `run_test_set` are split as drawn, with their schemas and tests, and the stage docs
  follow them, and the `evaluate` box is broken up, `fit` and `calibrate` into
  `models`, `score` into `scoring`, and `run_test_set` and `count_alarms` left in
  `evaluate`, all done 2026-09-22.

- Run `fit` and the stages after it on every log, on `train_sets/20260922-100444` and
  `test_sets/20260922-110745`. They passed on one day of logs in the smoke repos. Then
  score one other split, the first 25% of the time as test.
- Build the board application in the order of [board/docs/goal.md](board/docs/goal.md),
  due 2026-09-30. Step 3 there, the model, runs on the board and matches ONNX Runtime
  on 80 rows. Counting the calibration rows its difference moves across the threshold
  waits for `score`, and more rows wait for fetching them from the dataset. Step 4
  runs on the board. `can_path_from_flash` replays CAN frames through the slots, a
  preprocess task on a 0.1 s cyclic handler, scoring and detect, and report. FDCAN1 is
  on PB7 and PB8, and `can_bus_debug` prints what the bus receives and sends a frame
  every second. `can_bus_debug` sends and receives frames over the bus.
  `can_path_from_flash` has not run on the board yet. Then steps 2, 5 and 6.
- Decide whether the matched replay is the attack the windowed pair is measured on.
  `assemble.test_set --attack matched_replay` replays a PGN from a donor that held this
  log's speed and gear over the whole stretch. What no detector reads is a matched
  replay of TCO1, ETC1 or VDC2, whose values the matched speed and gear already fix or
  which no other PGN reads. The numbers are in
  [attack/measurements.md](attack/measurements.md).
- Run the pipeline on every log, and decide from `window_test_runs` whether a window
  model goes on the board. The two board items below come first.
  - On the board, put the rows in one ring in place of the row queue. preprocess writes
    it, and scoring and detect and a window scoring task read it under one mutex. Row
    flags go in an array beside it. Window scoring only copies windows for now. W and S
    belong in the window model's config header.
  - Add three tasks, alarm A before B.
    - A CAN task sends each start and end of alarm A as one frame on FDCAN1.
    - A cut task sits above the window model. When alarm A starts, it cuts the frames
      of the N rows before it out of a RAM ring and puts a MAC on them. The cut keeps
      the latest frames up to 8 KB. This is work at the moment the window model is
      needed, to show it late but not lost.
    - The lowest task stores the cut, and sends it and the alarm lines over UART with
      `tm_snd_dat`, which does not mask interrupts. `tm_printf` masks them.
    - The receive interrupt copies each frame into the ring.
    - The store is Flash bank 2 as 32 sectors of 8 KB. A cut goes to an erased sector
      at once. Erasing the oldest sector waits for a gap, about 2.7 min for 5 years
      at 8 h a day. [board/docs/h5_flash_memory.md](board/docs/h5_flash_memory.md) has
      the Flash facts.
- A script that compares scores.

## Tests

Run from the repository root.

```
python3 -m pytest
```
