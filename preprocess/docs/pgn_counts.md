# pgn_counts

Counts CAN frames per PGN over a stream of frames. Two independent counts, used
to decide which message types to keep and to see which ECUs send each.

## What the code does

- `count_pgns(frames)` returns a Counter mapping each PGN to how many frames it
  had. This is the message-type frequency on the bus.
- `count_pgn_senders(frames)` returns, per PGN, a Counter mapping each source
  address to how many frames it sent. This shows which ECUs produce each type.

Both walk a stream of `CanFrame` and decompose each identifier. They return data
only. Reading files and formatting the result are left to the caller.
