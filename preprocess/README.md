# preprocess

Turns the raw CAN bus logs recorded from the truck into inputs for the anomaly
detection model. Pure Python, run on a PC.

The logs are J1939/FMS CAN traffic. What a log looks like and the dataset facts
are in [docs/can_data.md](../docs/can_data.md).

## Steps

Each step is documented under [docs/](docs).

- [can_id_decompose](docs/can_id_decompose.md) splits a 29-bit CAN identifier
  into priority, PGN, and source address.

## Tests

Run from the repository root.

```
python3 -m pytest
```
