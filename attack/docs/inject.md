# inject

Picks a replay at random and applies it.

```python
inject(frames, rng, source_log)   # -> (frames, {pgn, start, stop, source}), or None
```

[replay](replay.md) says how to fake an attack. This says which one to fake. Which
message, when the attack starts, how long it runs, and which moment it copies are all
chosen at random, so that nothing here is picked to suit a detector.

`source` is a time in `source_log`. [replay](replay.md) says why that should not be
the log being attacked.

`inject` returns None when either log is too short, when the two share no message, or
when the replay wrote bytes the message already had. The last is no attack and should
not be counted as one that got away.

`rng` is a `random.Random`, so a seed gives the same attack twice and a test set can
be rebuilt.
