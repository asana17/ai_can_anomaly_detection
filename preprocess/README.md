# preprocess

Turns the raw CAN bus logs recorded from the truck into inputs for the anomaly
detection model. Pure Python, run on a PC.

The logs are J1939/FMS CAN traffic. What a log looks like and the dataset facts
are in [docs/can_data.md](../docs/can_data.md).

## Steps

In processing order. Each step is documented under [docs/](docs).

1. [can_log_loader](docs/can_log_loader.md) reads a CSV log into a stream of
   `CanFrame(timestamp, can_id, data)` records.
2. [can_id_decompose](docs/can_id_decompose.md) splits each frame's 29-bit
   identifier into priority, PGN, and source address.
3. [spn_decode](docs/spn_decode.md) extracts one SPN field from a payload as a
   physical value.
4. [pgn_counts](docs/pgn_counts.md) counts frames per PGN, and per source address
   within each PGN.
5. [pgn_intervals](docs/pgn_intervals.md) collects arrival intervals per
   (PGN, source address) stream.
6. [pgn_classify](docs/pgn_classify.md) flags proprietary PGNs, which have no
   public SPN definitions to decode.

## Tests

Run from the repository root.

```
python3 -m pytest
```
