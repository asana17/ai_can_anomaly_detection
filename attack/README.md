# attack

Synthesizes anomalies by modifying a normal CAN trace, to build the labeled test
set the detector is evaluated on. Anomalies are never mixed into training data.

Each module is documented under [docs/](docs).

- [spn_encode](docs/spn_encode.md) writes a physical value back into a payload,
  the inverse of preprocess spn_decode. Needed for value-level attacks.

## Tests

Run from the repository root.

```
python3 -m pytest
```
