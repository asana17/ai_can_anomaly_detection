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

### Detectors

The frames become one row of 17 signals every 100 ms. Three detectors read the rows.

| detector | what it catches |
|---|---|
| [rules](rules) | what can be written as a condition, like a value out of range or a gear that does not fit the speeds |
| row [autoencoder](models/docs/autoencoder.md) | how the signals of one row relate |
| window autoencoder | how the signals change over a window of rows |

The autoencoders learn normal rows only, on a PC. To test them, [attack](attack)
changes normal logs into synthetic anomalies, such as signals copied from another
moment or a bias that grows.

### Alarms

Rows and windows raise alarms in different ways, because one anomaly lasts a different
time in each. Take a signal that jumps and then holds the new value.

- Rows: the row model scores how the signals of the current row relate. The broken
  relation stays in the rows that follow. The alarm is raised when all of the last 10
  rows are suspicious, 10 in a row. This checks that the anomaly lasts, and a normal
  row that now and then looks wrong raises nothing.
- Windows: the window model is given the changes from row to row over the window and
  scores how well it rebuilds the change into the last row. The jump shows up as a
  change, but once the value holds the changes are normal again. The window can still
  score high for a while since the jump is in its past rows, but 10 in a row may not be
  reached. So one suspicious window is enough, and the alarm is on while one of the last
  10 rows has a suspicious window.

### Thresholds

A target is the false alarms an hour an alarm may raise on the calibration rows. These
rows come from the training logs, but the model never saw them. Each model's threshold
is the lowest score that keeps its alarm within its target there. The false alarms on
the test logs are not set by the target. They are measured.

- Rows: 1.5 an hour. The rows catch most attacks, so they take the larger share. The
  rules' own false alarms count against it.
- Windows: 0.5 an hour.

The two targets share out one budget. The
[evaluation](evaluate/docs/run_window_test_set.md) joins the row alarm and a window
alarm with OR, and counts alarm stretches that overlap as one. So the two together can
raise fewer false alarms than the sum.

On the test logs the alarms raise more than their targets. With the rows at 1.5 they
raise 2.0 to 2.6 an hour, and with the window autoencoder added 2.8 to 3.4, averaged
over folds 0 to 3 for each attack.

[settings.md](common/docs/settings.md#the-split-and-calibration-parameters) says how
the targets were set. [calibrate](models/docs/calibrate.md) and
[calibrate_windows](models/docs/calibrate_windows.md) say how the thresholds are taken.

### Models

Each autoencoder is compared with a linear model that reads the same input. PCA reads
one row, so the row autoencoder's gain over it is what nonlinearity buys. VAR reads a
window and shows what time alone buys, so the window autoencoder has to do better than
it.

The row autoencoder uses `hidden` 128 and `k` 8, chosen without looking at any attack.
`hidden` 128 because the board runs the heaviest model, which shows its load best. At
`k` 2 it rebuilds normal rows poorly. At `k` 16 only one of the 17 dimensions is
dropped, so a row passes through almost unchanged.
[fit](models/docs/fit.md#the-models-this-repository-fits) gives the thresholds behind
this.

The window autoencoder uses 1D convolutions, which share weights along time. A long
window then still fits in the board's Flash. At `hidden` 64 and `k` 16, 50 rows is the
longest window that fits the 100 ms period at 32 MHz.

No classifier is used. It needs labelled attacks, and the only attacks are the synthetic
ones, so it would learn those instead of unknown anomalies.

## Results

The counts are summed over folds 0 to 3 at seed 0, at k 10. Each cell is the attacks
caught and the false alarms an hour on the test logs.
[detection_table](evaluate/detection_table.py) made the tables from
`asana17/ai_can_anomaly_detection_runs`.

### What each detector catches

Each column joins models to the rules. Every threshold is set at the targets meant for
the board, in [Thresholds](#thresholds): 1.5 false alarms an hour for the row models
and 0.5 for the window models. PCA and the nonlinear AE are two row models. VAR and conv1d are two window models,
each added to the nonlinear AE.

| attack | what it does | worth catching | rules | rules + PCA | rules + nonlinear AE | rules + nonlinear AE + VAR | rules + nonlinear AE + conv1d |
|---|---|---|---|---|---|---|---|
| jittered_frozen_replay | holds one PGN's payload, jittered by steps the log itself took | 1992 | 569, 1.0/h | 603, 2.0/h | 985, 2.5/h | 994, 2.8/h | 1078, 3.1/h |
| matched_replay | copies one PGN from a log driven at the same speed and gear | 1557 | 370, 0.7/h | 393, 1.6/h | 760, 2.3/h | 770, 2.7/h | 857, 3.3/h |
| repeated_replay | sends a short stretch of one PGN again and again | 2174 | 696, 1.1/h | 723, 2.1/h | 1129, 2.6/h | 1135, 3.0/h | 1243, 3.4/h |
| replay | copies one PGN from another moment of another log | 3788 | 2156, 1.0/h | 2244, 2.0/h | 3091, 2.4/h | 3094, 2.7/h | 3191, 3.1/h |
| frozen_replay | holds the payload one PGN had at a random moment | 1889 | 1368, 0.7/h | 1393, 1.6/h | 1644, 2.2/h | 1644, 2.5/h | 1653, 3.0/h |
| playback | overwrites one signal with its values from another moment | 1892 | 455, 0.8/h | 498, 1.7/h | 1057, 2.4/h | 1060, 2.7/h | 1069, 3.2/h |
| ramp | adds a bias to one signal that grows over the attack | 779 | 136, 0.4/h | 138, 1.3/h | 393, 2.0/h | 393, 2.3/h | 400, 2.8/h |

PCA catches little more than the rules. The nonlinear AE catches 257 to 935 more. VAR
adds at most 10 to the nonlinear AE.

The table is read at `7da0b66`.

### Whether conv1d is worth its false alarms

conv1d is worth its share of the budget only if the nonlinear AE given the whole budget
catches less. So the nonlinear AE alone at a target of 2.0 an hour is set against the
nonlinear AE at 1.5 with conv1d at 0.5.

| attack | worth catching | rules + nonlinear AE at 2.0 | rules + nonlinear AE at 1.5 + conv1d at 0.5 |
|---|---|---|---|
| jittered_frozen_replay | 1992 | 1030, 2.6/h | 1078, 3.1/h |
| matched_replay | 1557 | 791, 2.5/h | 857, 3.3/h |
| repeated_replay | 2174 | 1173, 2.8/h | 1243, 3.4/h |
| replay | 3788 | 3141, 2.5/h | 3191, 3.1/h |
| frozen_replay | 1889 | 1658, 2.4/h | 1653, 3.0/h |
| playback | 1892 | 1091, 2.6/h | 1069, 3.2/h |
| ramp | 779 | 417, 2.2/h | 400, 2.8/h |

conv1d adds 48 to 70 on the four attacks that change how signals move over time. It
adds nothing where a value itself goes wrong.

The nonlinear AE alone at 2.0 is read at `c62fba2`, and the pair at `7da0b66`.

## Priorities

The window model is the heaviest, so it runs last. When an alarm starts, the frames
are stored first and the window model catches up later. The
[priorities of the board application](board/application/ai_can_anomaly_detection/README.md#tasks-and-priorities)
list every task in order.

## The board application

[ai_can_anomaly_detection](board/application/ai_can_anomaly_detection) is the main
application on the board. Its README has the frames it sends, the record in Flash,
the image size, the RAM left and the MCU's current.

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
- [THIRD_PARTY.md](THIRD_PARTY.md) lists the software and data from others with their
  rights holders, how to get them and their licenses, and states that their rights are
  cleared.

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
