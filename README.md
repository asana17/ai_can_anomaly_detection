# CAN anomaly detection

Detects unknown anomalies on a heavy duty truck's CAN bus (J1939/FMS), meant to run
on a small microcontroller (NUCLEO-H533RE).

Deterministic rules catch what can be written as an invariant, a value out of range
or two signals that must agree, like the engine and wheel speeds picking out the gear
the transmission reports. They are in [rules/](rules).

What no invariant covers is left to a model. None is built yet, and which one to
build is the question the TODO below works through. Whatever it turns out to be, it
trains offline on a PC on normal data only, then quantizes and runs on the device for
inference. Anomalies are synthesized from the normal data to test detection and never
enter training.

## Layout

- [dataset/](dataset) describes the logs and what profiling them found.
- [preprocess/](preprocess) turns raw CAN logs into model input vectors, by reading
  the log, decomposing the ID, decoding signals, and building a normalized vector.
- [assemble/](assemble) splits the logs by time and builds the train, validation,
  and test sets.
- [attack/](attack) synthesizes anomalies (masquerade) for a labeled test set.
- [rules/](rules) holds the deterministic checks that run before the model.
- `data/` holds the raw logs and is not tracked in git.

## TODO

- Synthesize anomalies by replacing a value with a real one from another time,
  then keep the ones every rule passes. Those are what the models have to catch.
- Compare PCA against a dense autoencoder on that set. Both read one instant, so
  this measures what nonlinearity alone is worth.
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
