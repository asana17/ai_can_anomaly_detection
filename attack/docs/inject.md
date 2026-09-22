# inject

Picks a replay at random and applies it.

```python
inject(frames, rng, source_log, spans=spans, source_spans=source_spans)
# -> (frames, {pgn, start, stop, source}), or None
```

[replay](replay.md) says how to fake an attack. This says which one to fake. Which
PGN, when the attack starts, how long it runs, and which moment it copies are all
chosen at random, so that nothing here is picked to suit a detector.

The attack lies in one of `spans` and copies from one of `source_spans`. Each is a
list of (start, end) times, the whole log when not given. The start is drawn evenly
over the times that leave the attack room.

`source` is a time in `source_log`. [replay](replay.md) says why that should not be
the log being attacked.

`inject` returns None when no span is long enough, when the two share no PGN, or
when the replay wrote bytes the PGN already had. The last is no attack and should
not be counted as one that got away.

`rng` is a `random.Random`, so a seed gives the same attack twice and a test set can
be rebuilt.
