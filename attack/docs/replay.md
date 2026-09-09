# replay

Gives a window of frames the payloads the same PGNs carried at another time,
in this log or in another.

```python
replay(frames, [65265, 65132], start=25.0, stop=30.0, source=5.0, source_log=other)
```

Every CCVS1 and TCO1 frame between t=25 and t=30 gets the bytes that PGN held at
t=5 in `source_log`, walking the source at the same pace. Frame times and counts do not
change, so the frame rate stays normal.

## Why replay rather than write a value

The bytes were observed, so each signal in a replayed PGN stays inside its range and
agrees with the others in that PGN. A written constant does neither, and
[range_check](../../rules/instant/docs/range_check.md) ends it. What replay breaks is the
agreement with the PGNs left alone.

Naming several PGNs moves them together, which is how an attack is aimed. Replay
CCVS1 alone and the two speeds disagree. Replay CCVS1 and TCO1 together and they
agree again, while the wheels still disagree with the engine.

## The source has to come from another log

Two moments of the same log are too alike to make an anomaly. Over 305 logs the
median distance between them is under 0.25 standard deviations for every PGN,
against 0.86 to 1.76 across logs.

That is not picking values a detector will catch. An attacker who writes back what
was nearly there has not attacked. The moment is still drawn uniformly, so how far it
lands is whatever the other log holds.

EBC1 stays weak either way, since the brake pedal reads zero on almost every row.

## What the rules catch

Replaying one PGN at a time, over a five second window in each of 20 logs taken
from 20 seconds earlier in the same log, counting only the windows where the bytes
changed. A same log source is the weak end above, so these are a floor.

| replayed | injections | [instant](../../rules/instant) catches | [change_limit](../../rules/rate/docs/change_limit.md) catches |
|---|---|---|---|
| CCVS1 wheel speed | 15 | 10 | 5 |
| TCO1 tachograph speed | 14 | 10 | 5 |
| ETC1 shafts | 19 | 6 | 0 |
| EEC1 engine | 19 | 4 | 0 |
| EEC2 pedal and load | 19 | 3 | 0 |
| ETC2 gears | 7 | 3 | 0 |
| EBC1 brake | 7 | 2 | 0 |
| VDC2 steering and yaw | 20 | 1 | 9 |
| LFE1 fuel rate | 19 | 0 | 0 |

Every PGN leaves injections the rules do not see, so replay is enough to build a
test set the models have to earn. Replaying LFE1 is invisible to all ten.

That says the rules as written do not cover these, not that no rule could. Fuel rate
is the one with evidence either way, since its tie to engine speed and torque is a
map rather than something to state.
