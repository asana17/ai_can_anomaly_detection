# Attack measurements

What the attacks are worth against the detectors, measured on 2026-09-23.

日本語版: [`measurements.ja.md`](measurements.ja.md)

A [replay](docs/replay.md) copies from any moment of a donor log. A matched replay,
which [replay](docs/replay.md) describes, copies from a moment the donor held the
attacked log's speed and gear all through the stretch. This says what each one costs a
detector.

## What was measured

### The data

| | |
|---|---|
| grid | `grids/20260922-093129`, 11,194 logs and 6,608,250 rows, 0.1 s apart |
| log split | `log_splits/20260922-100433`, 6,585 non-test and 4,609 test logs |
| logs attacked | 300 test logs drawn with seed 1 |
| donors | 200 non-test logs |
| instant model | the nonlinear autoencoder of `models/20260922-101102`, hidden 128 |
| threshold | `TARGET` of the 206,186 rows of `calibration_sets/20260922-100437` |
| windowed model | a PCA over ten rows, fitted here on non-test rows, same `TARGET` |
| window rules | 2,018,418 normal windows of the non-test logs |

### What landed

One log takes at most one attack.

| | replay | matched replay |
|---|---|---|
| logs with an attack in | 86 of 300 | 76 of 300 |
| moving rows the false positive rate is over | 38,455 | 33,079 |

An attack fails to land for three reasons. No moving stretch is long enough. No donor
moment matches. The replay wrote the bytes the PGN already had.

### What was not measured

Not the whole test set of 4,609 logs, and nothing was written to the Hub. The windowed
PCA is fitted for this measurement alone, so it stands for a windowed model and is not
one.

### Which attacks the rules fire on at all

Nothing is thrown away for tripping a rule, so the rules are measured on the same set as
the models. Whether an instant rule fires on a row an attack changed is worked out here
from the rules as they are, not stored with the set.

| | replay | matched |
|---|---|---|
| attacks | 86 | 76 |
| an instant rule fires | 42 | 3 |
| no rule fires | 44 | 73 |

## What the rules catch of a replay, one PGN at a time

Measured earlier, and kept here from [replay](docs/replay.md). One PGN over a five
second window in each of 20 logs, copied from 20 seconds earlier in the same log,
counting only the windows where the bytes changed. A same log source is the weak end,
so these are a floor.

| replayed | injections | instant catches | change_limit catches |
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

Every PGN leaves injections the rules miss, and LFE1 leaves all of them.

## Window rules

Six rules over ten rows, each stating something a stretch should hold. The first three
compare a pair [the rule measurements](../rules/measurements.md) rejected as an instant
rule, averaged over the window. The threshold is the value 1e-4 of normal windows sit
above. Away is the same rule over the same log, on the windows the attack does not
reach.

### What six window rules catch, and what they fire on with no attack there

| rule | fires on normal | replay | replay, away | matched | matched, away |
|---|---|---|---|---|---|
| engine_load against actual_engine_torque | 1e-4 | 12/86 | 0/86 | 9/76 | 0/76 |
| lateral_accel against speed times yaw_rate | 1e-4 | 1/86 | 0/86 | 0/76 | 0/76 |
| accel_pedal against driver_demand_torque | 1e-4 | 1/86 | 0/86 | 2/76 | 0/76 |
| a gear change with the clutch never slipping | 1.0e-3 | 6/86 | 6/86 | 0/76 | 2/76 |
| the brake down and the truck no slower | 5.9e-3 | 7/86 | 8/86 | 2/76 | 9/76 |
| the engine climbing with the pedal untouched | 1.5e-2 | 6/86 | 21/86 | 1/76 | 21/76 |

The first reads a matched replay as well as it reads a plain replay, 9 of 76 against
12 of 86, and never fires away from either. It was kept for that at first, which chose
a rule by the attack the windowed model is measured on. The first three were then
decided again from normal data alone, in the
[rule measurements](../rules/measurements.md). The first became
[torque_over_load](../rules/sequence/docs/torque_over_load.md), one sided, and the other
two were dropped.

The last three hold in ordinary driving, on engine braking and at a steady speed, and
fire away from the attack more often than on it.
