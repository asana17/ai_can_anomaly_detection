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

Converting a model for the board also needs [ST Edge AI Core](https://www.st.com/en/development-tools/stedgeai-core.html)
4.0.1 with its STM32 MCU component. It does not install through pip.

The logs go in `data/`, see [can_data/can_data.md](can_data/can_data.md#getting-it).

## Layout

- [can_data/](can_data) describes the logs and what profiling them found.
- [preprocess/](preprocess) turns raw CAN logs into rows, by reading the log,
  decomposing the ID, decoding signals, and putting them on a 100 ms grid.
- [assemble/](assemble) splits the logs by time and builds the train, calibration,
  and test sets.
- [attack/](attack) synthesizes anomalies for a labeled test set.
- [rules/](rules) holds the deterministic checks.
- [models/](models) holds the learned half, fit on normal rows only.
- [quantize/](quantize) writes the models out as ONNX for the NUCLEO-H533RE.
- [board/](board) holds our μT-Kernel applications for the NUCLEO-H533RE, one folder
  each. [board/docs/setup.md](board/docs/setup.md) builds and flashes one from nothing.
- [common/](common) holds the settings of a run and the rows built from the logs, which
  `evaluate`, `quantize` and `board` all read.
- [evaluate/](evaluate) runs the comparison and prints what each detector catches.
  What the runs found is in [evaluate/pc/results.md](evaluate/pc/results.md), and what
  quantizing their models costs is in [quantize/results.md](quantize/results.md).
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

- Add a board application that feeds the rows `board/rows.py` writes through a row
  queue to a task that echoes them over UART.
- Replace the echo with one generated model, and compare its outputs with ONNX
  Runtime's on the same rows.
- Port the preprocessing to C and feed real CAN frames to the same row queue.
- Add kinds of anomaly beyond replay to the attacked test set, designed against the
  rules.
- Add Isolation Forest beside the autoencoders, as a baseline that does not
  reconstruct.
- Restate [can_data/measurements.md](can_data/measurements.md) over every log.
- Settle whether the rules are a floor the models build on.
- Then widen to a stretch of time, VAR against a windowed autoencoder, if the instant
  models show it is worth doing.

## Tests

Run from the repository root.

```
python3 -m pytest
```
