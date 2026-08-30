# can_log_loader

Reads a CSV log of CAN frames into a stream of records. Each row is
`timestamp;id;dlc;data`. `load_can_log(path)` yields
`CanFrame(timestamp, can_id, data)`, one per row.

## What the code does

- Opens the file at `path`.
- Splits each row on `;` and builds a `CanFrame`.
  - `timestamp` is the wall-clock time parsed to epoch seconds. It is parsed as
    UTC so the value does not depend on the machine timezone.
  - `can_id` is the hex identifier as an integer, ready for `decompose_can_id`.
  - `data` is the payload, `dlc` bytes taken from the columns after `dlc`.

The loader does no decoding. It only turns text rows into typed frames. Splitting
the identifier and decoding signals are separate steps.
