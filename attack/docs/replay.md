# replay

Copies the payloads of some PGNs from another moment into a time window.

```python
replay(frames, [65265, 65132], start=25.0, stop=30.0, source=5.0, source_log=other)
```

| argument | |
|---|---|
| `frames` | the log to attack |
| `pgns` | the PGNs overwritten, the rest are left alone |
| `start`, `stop` | the window, in this log's times |
| `source` | the time in `source_log` the copy starts at |
| `source_log` | the log copied from, this one when not given |

Frame times and counts do not change. The bytes were observed, so what breaks is the
agreement with the PGNs left alone. Naming several PGNs moves them together.

The source comes from another log: over 305 logs, two moments of one log sit under 0.25
standard deviations apart for every PGN, against 0.86 to 1.76 across logs.

What each replay is worth against the rules and the models is in
[measurements](../measurements.md).

## random_replay.replay

Draws a replay and applies it.

```python
random_replay.replay(frames, rng, source_log, spans=spans, source_spans=source_spans)
# -> (frames, {pgn, start, stop, source}), or None
```

The PGN, the start, the length and the moment copied are all drawn at random, so none
is picked to suit a detector.

| argument | |
|---|---|
| `rng` | a `random.Random`. One seed gives one attack, so a test set can be rebuilt |
| `spans` | (start, end) times the attack may lie in, the whole log when not given |
| `source_spans` | (start, end) times in `source_log` it may copy from |

None comes back when no span leaves the attack room, when the two logs share no PGN,
and when the replay wrote the bytes the PGN already had.
