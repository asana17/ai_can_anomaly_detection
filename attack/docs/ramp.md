# ramp

Adds a bias to one signal of one PGN, growing from 0 at the start of the attack to its
full size at the stop.

```python
ramp(frames, rng, spans=spans)
# -> (frames, {pgn, start, stop, signal, bias}), or None
```

It picks the PGN, the start time and the length of the window as
[random_replay](replay.md#random_replayreplay) does, then one signal of the PGN. Gears
move in whole steps and are left out, so ETC2 is never picked.

The full size of the bias is drawn from 0 to `MOST`, 2, times the signal's std over the
log's own frames within `spans`, and its sign at random. Each frame of the PGN in the
window gets the share of it that the time since the start is of the window. A value is
kept within the range J1939 defines for it, and a reserved value is left as it is.

The frame times and counts do not change, so only the values move.

An attacker who knows a large change is caught moves the value a little at a time. At
the start the bias is too small for any single row to look wrong. The other signals
keep their real values, so the signal drifts away from those that move with it.

| argument | |
|---|---|
| `rng` | a `random.Random`. The same seed gives the same attack |
| `spans` | the times the window may start in. The whole log when not given |
| `most` | the most the bias reaches, in stds of the signal |

It returns None when no span is long enough for the window, the log carries no PGN to
fake, the signal holds no value within the spans, or no value changed.
