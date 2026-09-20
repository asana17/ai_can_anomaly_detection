# injected_frames

Writes the test logs with their attacks injected, frame by frame, as Parquet. They are
for sending the same attacks over a real CAN bus, which takes each message's ID, payload
and time, and the rows on the grid do not hold those.

```python
write_and_pass_frames(inject_frames(logs, rng, source_logs), dest, shard)
```

`write_and_pass_frames` writes the frames of each log [inject_frames](attack_set.md)
yields, and yields the log as it came, so the frames and the rows come from the same
draw of attacks. The files are `dest/test-NNNNN.parquet`, each holding about `shard`
frames.

| column | holds |
|---|---|
| `log` | the log the frame is from, the path it was read from |
| `timestamp` | epoch seconds |
| `can_id` | the 29-bit identifier |
| `data` | the payload bytes |
| `attacked` | True where the attack changed the payload |

An attack changes some payloads without moving any row, so `attacked` is not the label
to score a detector on. The label is on the rows, in [attack_set](attack_set.md). Which
attack a log holds is in the attack set's `attacks`, by `log`.

A row cut short in the source log is dropped on reading, so a log can hold a few frames
fewer than its file.
