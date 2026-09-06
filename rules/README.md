# rules

The deterministic layer. Each rule states an invariant the bus should hold and
reports where it does not, so the autoencoder is left with what no rule can express.

Documented under [docs/](docs).

- [range_check](docs/range_check.md) flags a signal outside the range J1939 defines
  for it.

A rule reads a `{name: value}` mapping, which
[frame_decode](../preprocess/docs/frame_decode.md) produces per frame and
[signal_state](../preprocess/docs/signal_state.md) accumulates across messages. The
same rule therefore runs on a recorded grid row and on the live state a device holds.

## Tests

Run from the repository root.

```
python3 -m pytest
```
