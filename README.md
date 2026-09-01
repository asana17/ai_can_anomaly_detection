# CAN anomaly detection

Detects unknown anomalies on a heavy duty truck's CAN bus (J1939/FMS), meant to run
on a small microcontroller (NUCLEO-H533RE).

Two layers share the work:

- Deterministic rules catch single signal faults, like a value out of range, an
  unknown message ID, or bad timing.
- An autoencoder catches multivariate faults, where each signal is plausible on its
  own but they do not agree with each other, like a speed that does not match the
  engine rpm.

The autoencoder is trained offline on a PC on normal data only, then quantized and
run on the device for inference. Anomalies are synthesized from the normal data to
test detection and never enter training.

## Layout

- [preprocess/](preprocess) turns raw CAN logs into model input vectors, by reading
  the log, decomposing the ID, decoding signals, and building a normalized vector.
- [attack/](attack) synthesizes anomalies (masquerade) for a labeled test set.
- [assemble/](assemble) splits the logs by time and builds the train, validation,
  and test sets.
- [docs/can_data.md](docs/can_data.md) describes the dataset.
- `data/` holds the raw logs and is not tracked in git.

## TODO

- Assemble the train, validation, and test arrays.
- Train the autoencoder and set the detection threshold.
- Add the deterministic rule layer.
- Quantize and run inference on the device.

## Tests

Run from the repository root.

```
python3 -m pytest
```
