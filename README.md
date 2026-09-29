# CAN anomaly detection

Multi-stage anomaly detection for a CAN bus, ordered by the task
priorities of μT-Kernel. Light models and evidence storage run before the heavy model,
which catches up later from the kept input.

## Overview

Watches a truck's CAN bus (J1939/FMS) on a NUCLEO-H533RE. It raises an alarm on CAN
when the signals go wrong. It keeps the frames before the alarm in Flash.

Watching the signals helps even with authentication such as SecOC, since a faulty or
taken over ECU still sends wrong values that pass it. The board has little CPU and RAM,
so the model cannot be large, and the tasks need priorities so that detection keeps up
with the incoming frames. The design and the results on the board are in the
[slides](https://docs.google.com/presentation/d/1hwYTSuzBjXj9xMCqELzK-VM9VE5GtPjH6FCRop7E4cI/edit?usp=sharing).

## Detection

The frames become one row of 17 signals every 100 ms. Three detectors read the rows.

| detector | what it catches |
|---|---|
| [rules](rules) | what can be written as a condition, like a value out of range or a gear that does not fit the speeds |
| row [autoencoder](models/docs/autoencoder.md) | how the signals of one row relate |
| window autoencoder | how the signals change over a window of rows |

The autoencoders learn normal rows only, on a PC. To test them, [attack](attack)
changes normal logs into synthetic anomalies, such as signals copied from another
moment or a bias that grows.

Rows and windows raise alarms in different ways.

- Rows: an attack makes many rows look wrong, and a normal row now and then looks
  wrong too. So the alarm waits for several suspicious rows among the last 10.
- Windows: an attack that changes how the signals move shows up in only a few windows,
  so one suspicious window is enough.

Each model's threshold is taken from calibration rows the model never saw. It is the
lowest score at which its alarm raises no more false alarms an hour than a target.

- Rows: 1.5 an hour. The rows catch most attacks, so they take the larger share. The
  rules' own false alarms count against it.
- Windows: 0.5 an hour. The alarm raised is the row alarm or a window alarm, so the two
  add up.

[settings.md](common/docs/settings.md#the-split-and-calibration-parameters) says how
the targets were set. [calibrate](models/docs/calibrate.md) and
[calibrate_windows](models/docs/calibrate_windows.md) say how the thresholds are taken.

Each autoencoder is compared with a linear model that reads the same input. PCA reads
one row, so the row autoencoder's gain over it is what nonlinearity buys. VAR reads a
window and shows what time alone buys, so the window autoencoder has to do better than
it. The window autoencoder uses 1D convolutions, which share weights along time. A long
window then still fits in the board's Flash.

Models not used, and why.

- A classifier needs labelled attacks. The only attacks are the synthetic ones, so it
  would learn those instead of unknown anomalies.
- Isolation Forest reads one row like PCA but splits one signal at a time. The attacks
  break how signals relate, which PCA reads.
- A recurrent model such as an LSTM carries a state from row to row, so it has to read
  every row in order. The window model runs last and catches up from the kept rows,
  which a model with no state can do from any window.

## Priorities

The window model is the heaviest, so it runs last. When an alarm starts, the frames
are stored first and the window model catches up later. The
[priorities of the board application](board/application/ai_can_anomaly_detection/README.md#tasks-and-priorities)
list every task in order.

## The board application

[ai_can_anomaly_detection](board/application/ai_can_anomaly_detection) is the main
application on the board. Its README has the frames it sends and the record in Flash.

| doc | what it has |
|---|---|
| [ai_can_anomaly_detection_tasks](board/lib/ai_can_anomaly_detection_tasks/README.md#priorities) | the tasks and their priorities |
| [board_guide_ja.md](guidelines/board_guide_ja.md) | building it from nothing and checking it with logs sent from a PC |

## Training on the PC

[pipeline](pipeline) runs every stage in one command. It makes the rows, trains and
calibrates the models, and evaluates them on the synthetic anomalies.
[pipeline_guide_ja.md](guidelines/pipeline_guide_ja.md) sets it up and runs it.

## Data

Every stage uploads to these Hugging Face repos by default. Reading them needs no login.

| repo | what it holds |
|---|---|
| [asana17/ai_can_anomaly_detection_data](https://huggingface.co/datasets/asana17/ai_can_anomaly_detection_data) | the rows and sets built from the logs |
| [asana17/ai_can_anomaly_detection_runs](https://huggingface.co/asana17/ai_can_anomaly_detection_runs) | the trained models, thresholds and results |

## Limitations

- The anomalies are synthetic, not copies of real attacks.
- All the logs come from one truck.

## Layout

- [can_data/](can_data) describes the logs and what profiling them found.
- [preprocess/](preprocess) turns raw CAN logs into rows, by reading the log,
  decomposing the ID, decoding signals, and putting them on a 100 ms grid.
- [assemble/](assemble) builds the grid, splits the test logs apart by time, and marks
  the calibration and train rows and the test rows with synthetic anomalies, each stage
  a directory on the Hugging Face Hub.
- [attack/](attack) synthesizes anomalies for a labeled test set.
- [rules/](rules) holds the deterministic checks.
- [models/](models) fits the row and window models on normal rows only, and gives
  each model the threshold a score counts as an anomaly above.
- [scoring/](scoring) scores a set of rows or windows with every model and marks the
  rows a rule hits.
- [detect/](detect) turns the models' scores and the rule hits into alarms.
- [deploy/](deploy) writes the models out as ONNX, quantizes them to int8, and turns
  them into C for the NUCLEO-H533RE.
- [board/](board) holds our μT-Kernel applications for the NUCLEO-H533RE, one folder
  each. [ai_can_anomaly_detection](board/application/ai_can_anomaly_detection) is the main
  application.
- [common/](common) holds the settings of a run and reads and writes the Hub
  directories every stage uses. [common/docs/settings.md](common/docs/settings.md)
  says how each parameter was set. [common/schemas](common/schemas)
  describes every JSON file a stage uploads, and the tests check each file a stage
  uploads against them.
- [evaluate/](evaluate) measures what each detector catches on the test rows and windows.
  What quantizing their models costs is in [deploy/results.md](deploy/results.md).
- [pipeline/](pipeline) runs every stage from the grid to the test run in one command,
  on HEAD's code in a worktree of its own, and says first what a run would build.
- [guidelines/](guidelines) has the how-to guides in Japanese, one for the pipeline and
  one for the board, with sample settings.
- [mtk3bsp2_samples](mtk3bsp2_samples) is the μT-Kernel BSP with the CAN driver, as a
  submodule.
- [tests/](tests) holds the tests, run with `python3 -m pytest` from the top.
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

## Tests

Run from the repository root.

```
python3 -m pytest
```
