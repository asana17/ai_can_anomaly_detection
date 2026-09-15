# CAN anomaly detection

Detects unknown anomalies on a heavy duty truck's CAN bus (J1939/FMS), meant to run
on a small microcontroller (NUCLEO-H533RE).

Deterministic rules catch what can be written as an invariant, a value out of range
or two signals that must agree, like the engine and wheel speeds picking out the gear
the transmission reports. They are in [rules/](rules).

What no invariant covers is left to a model. [PCA](models/docs/pca.md) is built, and a
dense autoencoder is next. A model trains offline on a PC on normal data only, then
quantizes and runs on the device for inference. Anomalies are synthesized from the normal data to test detection and never
enter training.

## Setup

Python 3.9. ONNX Runtime 1.19.2 is the last version that installs on it.

```
python3 -m pip install -r requirements.txt
```

Converting a model for the board also needs [ST Edge AI Core](https://www.st.com/en/development-tools/stedgeai-core.html)
4.0.1 with its STM32 MCU component. It does not install through pip.

## Layout

- [dataset/](dataset) describes the logs and what profiling them found.
- [preprocess/](preprocess) turns raw CAN logs into rows, by reading the log,
  decomposing the ID, decoding signals, and putting them on a 100 ms grid.
- [assemble/](assemble) splits the logs by time and builds the train, calibration,
  and test sets.
- [attack/](attack) synthesizes anomalies for a labeled test set.
- [rules/](rules) holds the deterministic checks.
- [models/](models) holds the learned half, fit on normal rows only.
- [evaluate/](evaluate) runs the comparison and prints what each detector catches.
  The last full run is in [evaluate/pc/results.md](evaluate/pc/results.md).
- `data/` holds the raw logs and is not tracked in git.

## Words

J1939's own terms, frame, PGN and SPN, are described in
[dataset/can_data.md](dataset/can_data.md). These are the ones this repo chose.

| word | what it is |
|---|---|
| log | one CSV capture, about a minute and 50,000 frames |
| signal | one decoded SPN under a name, such as `engine_speed`, 17 in all |
| row | every signal's latest value at one 100 ms tick |
| segment | a run of rows with no gap in time, broken between logs |
| residual | how far a row sits off the subspace a model fitted |
| block | one calibration window, in seconds above 5 km/h |

## TODO

- Run [evaluate](evaluate) over all 11,194 logs and put the result in
  [pca](models/docs/pca.md). Every run so far sampled 1,200 or fewer, which left
  under two hours of clean driving to count false alarms in.
- Add a dense autoencoder beside [pca](models/docs/pca.md) and compare the two on
  the attacked test set. Both read one instant, so the difference is what
  nonlinearity alone is worth. Score only while the truck moves.
- Settle whether the rules are a floor the models build on. Under one alarm
  definition for both, PCA has found more attacks than the rules and raised fewer
  false alarms in every run so far.
- Then widen to a stretch of time, VAR against a windowed autoencoder. A single
  instant holds few enough relations to write as rules, so this is where the
  autoencoder is expected to earn its place. Whether it is worth doing depends on
  what the instant pair shows.
- Quantize and run inference on the device.

## Tests

Run from the repository root.

```
python3 -m pytest
```
