# rules

The deterministic layer. Each rule states an invariant the bus should hold and
reports where it does not, so the autoencoder is left with what no rule can express.

Documented under [docs/](docs).

- [range_check](docs/range_check.md) flags a signal outside the range J1939 defines
  for it.
- [speed_agreement](docs/speed_agreement.md) flags the two vehicle speeds
  disagreeing, which no single signal's range would show.
- [shaft_ratio](docs/shaft_ratio.md) flags the output shaft turning at the wrong
  rate for the wheel speed.
- [gear_ratio](docs/gear_ratio.md) flags the engine and wheel speeds not matching
  the reported gear.
- [steering_sign](docs/steering_sign.md) flags the steering angle and the yaw rate
  turning opposite ways.
- [engine_off](docs/engine_off.md) flags a stopped engine with something it drives
  still running.
- [pedal_conflict](docs/pedal_conflict.md) flags both pedals pressed at once.
- [stopped_shaft](docs/stopped_shaft.md) flags the output shaft turning with the
  wheels stopped.
- [reverse_speed](docs/reverse_speed.md) flags reverse reported above a speed
  reverse cannot reach.

A rule reads a `{name: value}` mapping, which
[frame_decode](../preprocess/docs/frame_decode.md) produces per frame and
[signal_state](../preprocess/docs/signal_state.md) accumulates across messages. The
same rule therefore runs on a recorded grid row and on the live state a device holds.

## Tests

Run from the repository root.

```
python3 -m pytest
```
