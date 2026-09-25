# rules

The deterministic layer. Each rule states an invariant the bus should hold and
reports where it does not, so the autoencoder is left with what no rule can express.

Rules sit in one of two directories by what they need to read.
[instant/](instant) holds those that decide from a single moment. [sequence/](sequence)
holds those that also read the rows before in the run.

## instant

Each reads `raw`, one row per moment in physical units. Its columns are the signals
in the order `SIGNALS` in [signal_state](../preprocess/docs/signal_state.md) lists
them. It gives a True for each row it fires on.

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
- [reserved_moving](instant/docs/reserved_moving.md) flags a reserved value while the
  truck moves. The other rules do not judge one.

## sequence

Each reads grid rows together with the rows before them in their run.
Documented under [sequence/docs/](sequence/docs).

- [change_limit](sequence/docs/change_limit.md) flags a signal moving faster than the
  truck can move it.
- [torque_over_load](sequence/docs/torque_over_load.md) flags actual_engine_torque
  sitting above engine_load over the last second.

## Measurements

What the thresholds rest on, and the candidates that were measured and rejected, are
in [measurements](measurements.md).

## Tests

Run from the repository root.

```
python3 -m pytest
```
