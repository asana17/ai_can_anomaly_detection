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
| moving rows the false alarm rate is over | 38,455 | 33,079 |

An attack fails to land for three reasons. No moving stretch is long enough. No donor
moment matches. The replay wrote the bytes the PGN already had.

### How it is counted

| word | what it means |
|---|---|
| caught | a row the attack changed raised an alarm |
| false | the share of moving rows no attack reaches that raised one |
| `HOLD` | flags are ORed row by row, and n rows in a row raise the alarm, as [detect](../detect) does |
| a share | the attacks caught of the attacks there were, with its 95% interval |

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

## What the matched replay leaves

### What each detector catches of the 86 replays

Quiet is the same detector over the 44 replays no rule fires on.

| detector | `HOLD` 1 | 95% | false | `HOLD` 10 | 95% | false | quiet, `HOLD` 10 |
|---|---|---|---|---|---|---|---|
| instant rules | 42/86 = 0.49 | 0.39 to 0.59 | 0.0002 | 37/86 = 0.43 | 0.33 to 0.54 | 0.0000 | 0/44 |
| + windowed pca k=64 | 52/86 = 0.60 | 0.50 to 0.70 | 0.0127 | 47/86 = 0.55 | 0.44 to 0.65 | 0.0063 | 8/44 = 0.18 |
| + nonlinear ae k=8 | 69/86 = 0.80 | 0.71 to 0.87 | 0.0008 | 63/86 = 0.73 | 0.63 to 0.81 | 0.0000 | 22/44 = 0.50 |
| + nonlinear ae k=16 | 55/86 = 0.64 | 0.53 to 0.73 | 0.0020 | 51/86 = 0.59 | 0.49 to 0.69 | 0.0011 | 12/44 = 0.27 |

### What each detector catches of the 76 matched replays

Quiet is the same detector over the 73 matched replays no rule fires on.

| detector | `HOLD` 1 | 95% | false | `HOLD` 10 | 95% | false | quiet, `HOLD` 10 |
|---|---|---|---|---|---|---|---|
| instant rules | 3/76 = 0.04 | 0.01 to 0.11 | 0.0002 | 1/76 = 0.01 | 0.00 to 0.07 | 0.0000 | 0/73 |
| + windowed pca k=64 | 12/76 = 0.16 | 0.09 to 0.26 | 0.0055 | 8/76 = 0.11 | 0.05 to 0.19 | 0.0023 | 7/73 = 0.10 |
| + nonlinear ae k=8 | 25/76 = 0.33 | 0.23 to 0.44 | 0.0007 | 13/76 = 0.17 | 0.10 to 0.27 | 0.0000 | 12/73 = 0.16 |
| + nonlinear ae k=16 | 10/76 = 0.13 | 0.07 to 0.23 | 0.0018 | 5/76 = 0.07 | 0.03 to 0.14 | 0.0011 | 4/73 = 0.05 |

The rules hold 3 of the 76 matched replays against 42 of the 86 plain ones, and 1
against 37 once a flag has to last ten rows. On the attacks no rule fires on, everything
caught is the model's.

A model's threshold is `TARGET` of the calibration rows rather than one picked to match
the rules' alarm rate. The rates landed between 0.0010 and 0.0029 either way. The
windowed PCA rows are the exception at four to eight times that, so their gain is not
free.

### The two attacks are not the same attack

Fisher's exact test, two sided, at `HOLD` 10.

| detector | replay | matched | p |
|---|---|---|---|
| instant rules | 37/86 | 1/76 | 1.6e-11 |
| + windowed pca k=64 | 47/86 | 8/76 | 2.1e-09 |
| + nonlinear ae k=8 | 63/86 | 13/76 | 3.5e-13 |
| + nonlinear ae k=16 | 51/86 | 5/76 | 3.8e-13 |

Every detector reads the two apart, so the matched replay is a different attack and not
a replay drawn differently. The gap is not the samples being small.

### What the rules or the model catch at `HOLD` 10, by the PGN replayed

The instant rules or the nonlinear autoencoder k=8, held over ten rows.

| PGN | replay | matched |
|---|---|---|
| 61441 EBC1 | 3/4 | 0/1 |
| 61442 ETC1 | 11/12 | 0/13 |
| 61443 EEC2 | 10/14 | 7/15 |
| 61444 EEC1 | 6/6 | 5/11 |
| 61445 ETC2 | 5/7 | not replayed |
| 61449 VDC2 | 2/11 | 0/10 |
| 65132 TCO1 | 9/9 | 0/11 |
| 65265 CCVS1 | 9/9 | not replayed |
| 65266 LFE1 | 8/14 | 1/15 |

A matched replay of TCO1, ETC1 or VDC2 is never caught. The matched speed and gear already fix the first two, and no other PGN reads what
VDC2 carries, so a window may have nothing to recover there either. What is caught is
the engine side, EEC2 and EEC1, where a donor's own driving shows.

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

Only the first is worth keeping. It reads a matched replay as well as it reads a plain
replay, 9 of 76 against 12 of 86, and never fires away from either.

The last three hold in ordinary driving, on engine braking and at a steady speed, and
fire away from the attack more often than on it.

## What this leaves

The matched replay is an attack the rules catch 1 of 76 of at `HOLD` 10, the instant
model 13 of 76, and a linear windowed model 8 of 76. The windowed PCA reads 47 of 86
plain replays against the instant model's 63, so it is too weak to say whether a window
helps. A windowed autoencoder is the thing to build
next, beside VAR, which is where the [README](../README.md) TODO already points.
