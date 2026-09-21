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
- [models/](models) holds the learned half, fit on normal rows only.
- [detect/](detect) turns the models' scores and the rule hits into alarms.
- [deploy/](deploy) writes the models out as ONNX for the NUCLEO-H533RE.
- [board/](board) holds our μT-Kernel applications for the NUCLEO-H533RE, one folder
  each. [board/docs/setup.md](board/docs/setup.md) builds and flashes one from nothing.
  [board/docs/goal.md](board/docs/goal.md) is what the board is building towards, the
  TRON Programming Contest 2026 entry, and the order it is built in.
- [common/](common) holds the settings of a run and reads and writes the Hub
  directories every stage uses. [common/schemas](common/schemas)
  describes every JSON file a stage uploads. The tests check each file a stage
  uploads against them.
- [evaluate/](evaluate) runs the comparison and prints what each detector catches.
  What the runs found is in [evaluate/pc/results.md](evaluate/pc/results.md), and what
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
  3. The model scores the moving rows no rule hit.
  4. `detect` compares the scores with the threshold, adds the rule flags, and holds
     them over `HOLD`.

  `score` runs the scoring pipeline over a set of rows and keeps each row's scores and
  rule flags. It scores the calibration rows for `calibrate`, which takes the
  threshold from them, and the test set's rows for `pc.detect`, so a new threshold or
  `HOLD` needs no rescoring. About 33 MB and 430 MB for 40 models, reckoned from the
  grid's row counts. Rows are selected by mask and never cut out, since `HOLD` counts
  rows in a row. No function joins the steps.

  The stages after it.

  ```mermaid
  flowchart TB
      grid --> split["split_test_logs"] --> calibration_set & test_set
      calibration_set -- blocks --> train_set
      train_set --> train[(train set)]
      calibration_set --> calibration[(calibration set)]
      test_set --> test[(test set)]
      train --> fit
      fit -- scale, models --> score
      calibration --> score
      test --> score
      score -- calibration set scores --> calibrate
      score -- test set scores, rule flags --> detect["pc.detect"]
      calibrate -- thresholds --> detect
      detect -- alarms --> counting["counting<br/>caught, alarms per hour"]
      fit -- models --> export["deploy.export"] -- float ONNX --> quantize["deploy.quantize"]
      train -- representative rows for int8 --> quantize
      fit -- scale for the representative rows --> quantize
      quantize -. int8 ONNX .-> score
  ```

  The same two parts run on the PC and on the board.

  | part | steps | on the PC | on the board |
  |---|---|---|---|
  | scoring pipeline | `preprocess`, `rules`, the model | `score` | in C |
  | `detect` | threshold, OR the rule flags, `HOLD` | `pc.detect` | in C |

  What still differs from today's code. `moving` and `Scale` are in `preprocess`, the
  train rows drop rule hits, the rules run over columns with numpy, and `fit` keeps the
  scale in the models, `detect` holds step 4, and `split_test_logs`, `calibration_set`,
  `train_set` and `test_set` build the sets, all done 2026-09-22. Rows 11 to 13 are to
  be fixed along with the rest.

  | # | what | today | after |
  |---|---|---|---|
  | 4 | calibration rows | moving only in `calibration_set`, `calibrate` drops rule hits | rules applied in `score` |
  | 8 | scoring stage | `pc.score` scores and counts | `score` writes `scores/`, `pc.detect` writes `detections/` |
  | 9 | `calibrate` | selects rows, scores, takes the quantile | reads scores, takes the quantile |
  | 10 | counting | `counting.py`, beside what a detector reads | counting only |
  | 11 | JSON Schemas | `detection` and others for today's dirs | match `scores/`, `detections/`, `thresholds/`, `models/` |
  | 12 | tests | e.g. `test_train_set.py` checks `scale.npy`, `test_score.py` patches `fetch_scale` | follow rows 1 to 11 |
  | 13 | stage docs | `evaluate/docs/*` | follow rows 1 to 11, place `pc_run.md` |

  - Build the log split and the three sets again. Their inputs changed, so no
    `--rebuild` is needed. The stages after them follow the new paths.
  - Keep the counting of what was caught apart from `persistent`, for the board to use
    too.
  - Split `evaluate.pc.score` into `score`, writing `scores/`, and `pc.detect`,
    writing `detections/`. `calibrate` then reads scores.
  - Redraw the diagram in [evaluate/README.md](evaluate/README.md) for the new layout.
    A diagram of the old layout is in `git stash`, stale.
  - `evaluate` is not a unit of the design, only a box the stages sit in. Decide where
    `fit`, `calibrate`, `score`, `pc.detect` and counting go, and break it up.
- Fold `common/hf_upload.py` into `common/hub_dirs.py`.
- Draw the attacks over the test span's time rather than one per log. One per log puts
  most attacks where the truck stands, and four times as many per moving hour in the
  logs that move least. Measure first whether that shifts a model's numbers, from
  `caught` in a score. The rules catch the same share in every band of a log's moving
  seconds.
- Record in `injected.json` which donor log each attack copied from. `source` is a time
  in that log, and nothing says which log it is. Add `donor` to its schema then.
- Build the dataset in the new layout, then check the whole path on a few logs, then
  score one other split, the first 25% of the time as test. `fit` and the stages after
  it wait for the `evaluate` item.
- Build the board application in the order of [board/docs/goal.md](board/docs/goal.md),
  due 2026-09-30. Step 3 there, the model, runs on the board and matches ONNX Runtime
  on 80 rows. Counting the calibration rows its difference moves across the threshold
  waits for `score`, and more rows wait for fetching them from the dataset. Step 4 is
  under way. The nine instant rules are C headers in `board/lib/rules/`, matched with
  `rules/` on the PC. What else goes to C is listed in goal.md, What goes to C. Next
  is the threshold and `HOLD` of `detect/alarm.py` in C, then the anomaly task.
- Add kinds of anomaly beyond replay to the attacked test set, designed against the
  rules.
- Add Isolation Forest beside the autoencoders, as a baseline that does not
  reconstruct.
- Restate [can_data/measurements.md](can_data/measurements.md) over every log.
- Settle whether the rules are a floor the models build on.
- Then widen to a stretch of time, VAR against a windowed autoencoder, if the instant
  models show it is worth doing.
- A script that compares scores.
- Rerun the linear autoencoder checks in the runs repo's `checks/` from a committed
  script, on the current dataset.

## Tests

Run from the repository root.

```
python3 -m pytest
```
