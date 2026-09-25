# torque_over_load

Flags actual_engine_torque sitting above engine_load over the last second.

```python
hits(raw, position)   # -> True where torque minus load, averaged, is above LIMIT
ROWS                  # -> 10, the rows averaged
LIMIT                 # -> 3.5, in % points
```

engine_load is torque as a share of the most the engine gives at its present speed.
actual_engine_torque is a share of one reference torque. So load sits at or above
torque, and only torque above load breaks the relation. On a single normal row torque
still rises up to 47 points above load, and averaging over ten rows brings that down to
5.3. Why single rows cross is not measured. EEC1 and EEC2 arriving at different times
while torque changes is a guess.

The caller gives each row its place in its run, which is what separates this from the
rules in [instant](../../instant). It is kept out of `rule_hits`, the floor of the
instant pair, since the instant models do not see the rows before.

## The rows it reads

A run is the moving rows of one grid segment, one tick apart. A hit does not end it.
This is the run the board's row ring keeps. The first nine rows of a run are not judged,
and neither is a window with a NaN in it.

## How it was picked

Measured over every log on grid `20260922-093129`, 2,757,787 moving rows. The drift is
the p99 of the mean of torque minus load, and the range is the p99 of load, 87 points.
The threshold is the value 1e-4 of the windows sit above.

| rows averaged | drift | drift over range | threshold | rows not judged |
|---|---|---|---|---|
| 1 | 2 | 2.3% | 15 | 0 |
| 5 | 1.2 | 1.4% | 6 | 1.1% |
| 10 | 0.8 | 0.9% | 3.5 | 2.4% |
| 20 | 0.35 | 0.4% | 1.55 | 4.9% |
| 50 | 0.08 | 0.1% | 0.56 | 11.9% |

The drift falls steadily with the rows averaged and shows no point to stop at. Ten
rows is a judgement. The threshold is a quarter of the one-row figure, and 2.4% of
moving rows go unjudged. The number does not follow the windowed model's window, which
is picked on its own grounds.

It fires on 232 rows, 229 of them rows no other rule fires on. With change_limit and
the instant rules the rules fire on 1,942 of 2,757,787 moving rows, 0.0704%, under the
0.1% the rules are held to.

## Where it came from

The rule was first thought of after the matched replay was built, as one of six rules
over ten rows in [the attack measurements](../../../attack/measurements.md). It was
kept then because it caught 9 of 76 matched replays. That chose it by an attack, and
by the attack the windowed model is measured on. So the choice was made again from
normal data alone, as told in [measurements](../../measurements.md). The one-sided form,
the ten rows and the threshold all come from that.

## On the test set

Measured after the choice and not used for it. Test set `20260925-120833`, 1,240 plain
replays, a replay caught when a row it changed is flagged, with no `HOLD`.

| | rules before | with torque_over_load |
|---|---|---|
| EEC1 replays caught | 144 of 177 | 165 of 177 |
| EEC2 replays caught | 20 of 132 | 94 of 132 |
| all replays caught | 804 of 1,240 | 899 of 1,240 |
| moving rows flagged more than 10 rows from any replay | 621 of 606,101, 0.1025% | 694, 0.1145% |

The other PGNs are caught as often as before. Rows up to 10 rows after a replay are
left out of the last line, because the rule's window still reaches the replay there.
