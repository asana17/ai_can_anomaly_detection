# pgn_intervals

Collects the arrival intervals (gaps between consecutive frames) for each
(PGN, source address) stream. Feeds the period threshold in the rule layer and
the period-deviation feature in stage 2.

## What the code does

- `arrival_intervals(frames)` walks a stream of `CanFrame` in arrival order and,
  for each (PGN, source address), records the time gap from the previous frame of
  that same stream.
- The key is `(pgn, source_address)` because each ECU sends a PGN at its own rate.
  Mixing senders would understate the true period.
- It expects one contiguous capture. Intervals are not computed across file
  boundaries, where the gap between captures is not a real bus interval.

It returns raw intervals. Summaries such as the median or percentiles are left to
the caller.
