# inject

Picks a replay at random and applies it.

```python
inject(frames, rng)   # -> (frames, {pgn, start, stop, source}), or None
```

[replay](replay.md) says how to fake an attack. This says which one to fake. Which
message, when the attack starts, how long it runs, and which moment it copies are all
chosen at random, so that nothing here is picked to suit a detector.

`inject` returns None in two cases. The log may be too short to hold both the attack
and the moment it copies. Or the replay may have written bytes the message already
had, which is no attack at all and should not be counted as one that got away.

`rng` is a `random.Random`, so a seed gives the same attack twice and a test set can
be rebuilt.
