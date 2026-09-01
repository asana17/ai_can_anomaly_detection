# pgn_intervals

Collects the arrival intervals (gaps between consecutive frames) for each
(PGN, source address) stream.

```python
arrival_intervals(frames)   # -> {(pgn, source_address): [gap, ...]}
```

The key is `(pgn, source_address)` because each ECU sends a PGN at its own rate.
Mixing senders would understate the true period. Intervals are not computed across
file boundaries, where the gap between captures is not a real bus interval.
