# attack

Synthesizes anomalies by modifying a normal CAN trace, to build the labeled test
set the detector is evaluated on. Anomalies are never mixed into training data.

Documented under [docs/](docs).

## Attacks

- [masquerade](docs/masquerade.md) overwrites signals in place within a time
  window, keeping the frame timing normal. Nothing calls it yet.
- [replay](docs/replay.md) gives a stretch of frames the payloads those PGNs
  carried at another time, so the written values are ones the bus really produced.
- [inject](docs/inject.md) picks one of those at random, for building a test set.

## Utilities

- [spn_encode](docs/spn_encode.md) writes a physical value into a payload, the
  inverse of preprocess spn_decode. Used by value-level attacks.

## Tests

Run from the repository root.

```
python3 -m pytest
```
