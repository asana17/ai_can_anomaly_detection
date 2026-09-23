# replay

Copies payloads from one moment of a log into a time window of the log being attacked.

```python
replay(frames, [65265, 65132], start=25.0, stop=30.0, source=5.0, source_log=other)
```

| argument | |
|---|---|
| `frames` | the log being attacked |
| `pgns` | the PGNs to overwrite. Every other PGN keeps its payloads |
| `start`, `stop` | the window, in the attacked log's own times |
| `source` | the time in the donor log the copy starts at |
| `source_log` | the donor log. The attacked log itself when not given |

The frames keep their original times, and none are added or removed.

The copied values were recorded on a real drive, so each one is a value the truck can
produce. A range check will not catch them. What the attack breaks is the match between
the copied PGNs and the PGNs left alone.

The donor log should not be the attacked log. Two moments of one log are too much
alike. Over 305 logs the distance between two moments of one log stays under 0.25
standard deviations. Between two logs it is 0.86 to 1.76.

[measurements](../measurements.md) reports what each kind of replay is worth against
the rules and the models.

## random_replay.replay

Picks one replay at random and writes it.

```python
random_replay.replay(frames, rng, source_log, spans=spans, source_spans=source_spans)
# -> (frames, {pgn, start, stop, source}), or None
```

It picks the PGN, the start time, the length of the window, and the moment in the donor
log. All four are random, so no choice is made to suit a detector.

| argument | |
|---|---|
| `rng` | a `random.Random`. The same seed gives the same attack |
| `spans` | the times the window may start in. The whole attacked log when not given |
| `source_spans` | the times in the donor log the copy may start at |

It returns None in three cases. No span is long enough for the window. The two logs
carry no PGN in common. The payloads written were already there.

## matched_replay.replay

Picks a replay from a donor log that was being driven like the attacked log.

```python
matched_replay.replay(frames, rng, donors, rows=rows, period=period, spans=spans)
# -> (frames, {pgn, start, stop, source}), or None
```

A moment in a donor log matches when two things hold on every row of the window. The
donor's wheel speed stays within `tolerance` of the attacked log's. The donor is in the
same gear.

Speed and gear decide most of the other signals in a row. The shaft speeds follow the
wheel speed. The engine speed follows it through the gear ratio. The tachograph reads
the same speed again. Matching the two therefore leaves a row that an instant rule or
an instant model reads as normal.

The pedal, the torque, the fuel rate and the steering still come from another drive.
Those only look wrong when several rows are read together.

| argument | |
|---|---|
| `donors` | one (rows, frames_of) per donor log. Its rows by time, and what loads its frames |
| `rows` | the attacked log's rows by time |
| `period` | the seconds between two rows |
| `tolerance` | the speed the donor may differ by. `MAX_DISAGREEMENT` by default |

It looks in every donor log and picks one matching moment at random. It never fakes
CCVS1 or ETC2, which carry the speed and the gear it matches on. It returns None in the
same three cases as `random_replay.replay`, and when no moment matches.
