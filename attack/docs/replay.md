# replay

Gives a window of frames the payloads the same messages carried at another time.

```python
replay(frames, [65265, 65132], start=25.0, stop=30.0, source=5.0)
```

Every CCVS1 and TCO1 frame between t=25 and t=30 gets the bytes that message held
20 seconds earlier, walking the source at the same pace. Frame times and counts do
not change, so the message rate stays normal.

## Why replay rather than write a value

The bytes were observed, so each signal in a replayed message stays inside its range
and agrees with the others in that message. A written constant does neither, and
[range_check](../../rules/instant/docs/range_check.md) ends it. What replay breaks is the
agreement with the messages left alone.

Naming several messages moves them together, which is how an attack is aimed. Replay
CCVS1 alone and the two speeds disagree. Replay CCVS1 and TCO1 together and they
agree again, while the wheels still disagree with the engine.

## Choosing the source

Replaying a moment like the one it replaces produces no anomaly. In four of twelve
logs a source 20 seconds earlier left the wheel speed unchanged and no rule fired.

Distance in time will not fix that, since 20 seconds is nothing on a cruise and a lot
mid shift. Pick the source at random, and drop a replay that changed no bytes.

## What the rules catch

Replaying one message at a time, over a five second window in each of 20 logs taken
from 20 seconds earlier, counting only the windows where the bytes actually changed.

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

Every message leaves injections the rules do not see, so replay is enough to build a
test set the models have to earn. Replaying LFE1 is invisible to all ten.

That says the rules as written do not cover these, not that no rule could. Fuel rate
is the one with evidence either way, since its tie to engine speed and torque is a
map rather than something to state.
