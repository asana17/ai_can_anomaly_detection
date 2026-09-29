# CAN anomaly detection

Watches a heavy duty truck's CAN bus (J1939/FMS) on a NUCLEO-H533RE, raises an alarm
on CAN when the signals go wrong, and keeps the frames before the alarm in Flash for
investigation.

The frames become one row of 17 signals every 100 ms. Three detectors read the rows.

| detector | what it catches |
|---|---|
| [rules](rules) | what can be written as a condition, like a value out of range or the engine and wheel speeds disagreeing with the reported gear |
| row [autoencoder](models/docs/autoencoder.md) | how the signals of one row relate, beyond what the rules list |
| window autoencoder | how the signals change over a window of rows |

The autoencoders train on a PC on normal rows only and run on the board. Attacks are
synthesized from normal logs to test detection and never enter training.

On the board, making rows, the rules and the row model, the alarm and storing the
frames come before the window model, which is the heaviest. The window model waits
while they run and catches up from the rows kept for it. The design and the results
on the board are in the
[slides](https://docs.google.com/presentation/d/1hwYTSuzBjXj9xMCqELzK-VM9VE5GtPjH6FCRop7E4cI/edit?usp=sharing).

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
  [ai_can_anomaly_detection](board/application/ai_can_anomaly_detection) is the TRON
  Programming Contest 2026 entry.
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

## Tests

Run from the repository root.

```
python3 -m pytest
```
