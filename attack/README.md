# attack

Synthesizes anomalies by modifying a normal CAN trace, to build the labeled test
set the detector is evaluated on. Anomalies are never mixed into training data.

Documented under [docs/](docs).

## Attacks

- [spoof](docs/spoof.md) overwrites one signal to a fixed value within a time
  window.

## Utilities

- [spn_encode](docs/spn_encode.md) writes a physical value into a payload, the
  inverse of preprocess spn_decode. Used by value-level attacks.

## Tests

Run from the repository root.

```
python3 -m pytest
```
