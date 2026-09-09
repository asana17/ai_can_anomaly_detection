# signal_state

Keeps the latest value of each tracked signal, so signals that arrive in separate
PGNs can be read together as one row.

## Example

```python
state = SignalState()
state.update(decode_frame(61444, eec1_data))   # updates engine_speed, torque
state.update(decode_frame(65265, ccvs1_data))  # updates wheel_speed
state.row()        # every signal's latest value, in SIGNALS order
state.values()     # the same by name, leaving out any not yet seen
```

## Details

The target signals live in different PGNs that arrive at different times, so at any
instant only one of them has just changed. `SignalState` remembers the most recent
value of each, so reading it gives all signals aligned to the same moment.

`update` takes a `{name: value}` dict and overwrites those signals. `row`
returns the values in the fixed `SIGNALS` order, which is the layout the model
sees. A signal not yet seen is `None`, and `ready()` is True once all are set.
