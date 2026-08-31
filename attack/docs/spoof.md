# spoof

Spoofing means falsifying a signal's value on the bus. This module implements the
simplest form. One signal is held at a fixed value within a time window. Richer
spoof variants (multiple signals, or a non constant value) can be added later.

## What the code does

`spoof(frames, pgn, name, value, start, stop)` returns a new trace where every
frame of `pgn` whose timestamp is in `[start, stop]` has its `name` signal set to
`value` with spn_encode. All other frames are returned unchanged.
