# preprocess

Turns the raw CAN bus logs recorded from the truck into inputs for the anomaly
detection model. Pure Python, run on a PC.

The logs are J1939/FMS CAN traffic. What a log looks like and the dataset facts
are in [docs/can_data.md](../docs/can_data.md).

## Modules

Each module is documented under [docs/](docs).

### frames: log to decoded signals

1. [can_log_loader](docs/can_log_loader.md) reads a CSV log into a stream of
   `CanFrame(timestamp, can_id, data)` records.
2. [can_id_decompose](docs/can_id_decompose.md) splits a frame's 29-bit
   identifier into priority, PGN, and source address.
3. [spn_decode](docs/spn_decode.md) extracts one SPN field from a payload as a
   physical value, using the field definitions in [spn_spec](docs/spn_spec.md).
4. [frame_decode](docs/frame_decode.md) decodes all of a frame's SPNs into a
   `{name: value}` dict.

### profile: measure the data

- [pgn_counts](docs/pgn_counts.md) counts frames per PGN, and per source address
  within each PGN.
- [pgn_intervals](docs/pgn_intervals.md) collects arrival intervals per
  (PGN, source address) stream.
- [pgn_classify](docs/pgn_classify.md) flags proprietary PGNs, which have no
  public SPN definitions to decode.

### features: signals to model input

- [signal_state](docs/signal_state.md) keeps the latest value of each signal, so
  they can be read together as one snapshot.
- [grid_sample](docs/grid_sample.md) samples the signal state on a fixed time grid
  into a regular series of vectors.

## Tests

Run from the repository root.

```
python3 -m pytest
```
