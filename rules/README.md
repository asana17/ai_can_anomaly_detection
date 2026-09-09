# rules

The deterministic layer. Each rule states an invariant the bus should hold and
reports where it does not, so the autoencoder is left with what no rule can express.

Rules sit in one of two directories by what they need to read.
[instant/](instant) holds those that decide from a single moment. [rate/](rate) holds
those that need the previous reading and the time since, because they cannot be
called the same way and they belong to a different half of the evaluation.

## instant

Each reads a `{name: value}` mapping, which
[frame_decode](../preprocess/docs/frame_decode.md) produces per frame and
[signal_state](../preprocess/docs/signal_state.md) accumulates across PGNs. The
same rule therefore runs on a recorded grid row and on the live state a device holds.

Documented under [instant/docs/](instant/docs).

- [range_check](instant/docs/range_check.md) flags a signal outside the range J1939
  defines for it.
- [speed_agreement](instant/docs/speed_agreement.md) flags the two vehicle speeds
  disagreeing, which no single signal's range would show.
- [shaft_ratio](instant/docs/shaft_ratio.md) flags the output shaft turning at the
  wrong rate for the wheel speed.
- [gear_ratio](instant/docs/gear_ratio.md) flags the engine and wheel speeds not
  matching the reported gear.
- [steering_sign](instant/docs/steering_sign.md) flags the steering angle and the yaw
  rate turning opposite ways.
- [engine_off](instant/docs/engine_off.md) flags a stopped engine with something it
  drives still running.
- [pedal_conflict](instant/docs/pedal_conflict.md) flags both pedals pressed at once.
- [stopped_shaft](instant/docs/stopped_shaft.md) flags the output shaft turning with
  the wheels stopped.
- [reverse_speed](instant/docs/reverse_speed.md) flags reverse reported above a speed
  reverse cannot reach.

## rate

Each reads the current mapping, the one before it, and the seconds between.
Documented under [rate/docs/](rate/docs).

- [change_limit](rate/docs/change_limit.md) flags a signal moving faster than the
  truck can move it.

## Measurements

What the thresholds rest on, and the candidates that were measured and rejected, are
in [measurements](measurements.md).

## Tests

Run from the repository root.

```
python3 -m pytest
```
