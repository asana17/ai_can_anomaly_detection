# Measurements

What profiling the logs found. The dataset itself is described in
[can_data](can_data.md). The per PGN figures come from
[summary](../preprocess/docs/summary.md), which reruns them on any set of files.

日本語版: [`measurements.ja.md`](measurements.ja.md)

## Profiling findings (1,200 files across all four parts, 60,001,200 frames)

- **57 unique PGNs.** One file carries 52 to 57 of them (median 55), and 52 appear
  in every file. **10 source addresses**, of which `230`, the main powertrain ECU,
  sends 75.9% of all frames. The next five send 3.5 to 3.9% each.
- DLC distribution: `8` is **98.22%**, then `4` 1.19%, `1` 0.59%, `3` under 0.01%.
- **41 PGNs are public and 16 are proprietary**, carrying 76.1% and 23.9% of frames.
  The proprietary ones have no published SPN definitions, so they cannot be decoded.
  See [pgn_classify](../preprocess/docs/pgn_classify.md).
- **EEC1, EEC2, CCVS1 and LFE1 are in 100% of files** (share of frames, rate):
  - `EEC1` (61444), 5.91%, every 20 ms, engine speed and engine torque
  - `EEC2` (61443), 2.36%, every 50 ms, accelerator pedal and engine percent load
  - `CCVS1` (65265), 1.18%, every 100 ms, wheel based vehicle speed
  - `LFE1` (65266), 1.18%, every 100 ms, engine fuel rate
- `ETC2` (61445) is in every file at 10 Hz, carrying SPN 524 selected gear and SPN
  523 current gear. Observed values are `-1` reverse, `0` neutral and `1` to `12`,
  with `0xFF` not available in 0.68% of frames.
- **Multi packet transport is small and always present.** TP.CM (60416) is 0.25% of
  frames and TP.DT (60160) is 0.74%. Neither carries the target SPNs.

Rates are the median gap per (PGN, source address) stream, not frames divided by
file duration. The latter understates any file that contains a gap, which is how an
earlier profile of one file put EEC1 at 5 Hz instead of its actual 50 Hz.

## Gearbox

A 12 speed box. Grouping the gridded rows by current gear, engine speed over wheel
speed lands on one ratio per gear.

| gear | 12 | 11 | 10 | 9 | 8 | 7 | 6 | 5 | 4 |
|---|---|---|---|---|---|---|---|---|---|
| rpm per km/h | 15.12 | 19.38 | 24.88 | 31.62 | 41.12 | 52.4 | 66.1 | 84.4 | 107.9 |

Each step is 1.28, and the same ratios appear in all four parts, which is what one
fixed gearbox should give. The gear reported in ETC2 matches these to within 0.9%
for gears 5 to 12. Between the ratios the histogram is nearly empty, 0.02% to 1.1%
of the neighbouring peak, so a pair of engine and wheel speeds either sits on a gear
or is impossible.

Top gear at 15.12 also matches the ETC1 output shaft, which turns at 15.25 rpm per
km/h, so twelfth is close to direct.

## What the truck is doing

Over 1,200 files the grid yields 704,493 rows.

| state | share |
|---|---|
| engine off | 16.3% |
| idling, engine on and stopped | 32.2% |
| moving | 51.5% |

Gear coverage is far from even. Of 251,894 steady moving rows, top gear holds 48,078
and the low gears around 1,000 each, a spread of about 44 to 1. A model trained on
this sees the low gears rarely, so results should be read per gear rather than
pooled.

## Gaps between frames

Of 60,000,000 consecutive frame gaps, 76.9% fall under 1 ms and 23.1% between 1 and
10 ms. Only 27 land between 10 and 100 ms, and **none at all between 100 ms and
2 seconds**. Sixty gaps exceed 2 seconds, and those are the recording breaks.

The distribution is empty over more than a decade, so any threshold placed in that
band separates the same 60 breaks from normal traffic. This is what
[grid_sample](../preprocess/docs/grid_sample.md) uses `max_hold` for, and why its
value is not delicate.

## Values outside their range

Every decoded value is checked against the J1939 range `spn_spec` records for it.
Across 100 files that is 5,034,836 values over 17 signals, and none of them fall
outside. The rule layer's range check therefore starts from no false positives on
this data.

## Rules on normal data

Every rule in [rules](../rules/README.md) over 584,694 evaluations, one per decoded
frame. The share is of all of them, so it is lower than the rate each rule's own doc
gives over the evaluations it applies to.

| rule | fires | share |
|---|---|---|
| range_check | 0 | 0% |
| speed_agreement | 39 | 0.0067% |
| shaft_ratio | 26 | 0.0044% |
| gear_ratio | 12 | 0.0021% |
| steering_sign | 68 | 0.0116% |
| engine_off | 0 | 0% |
| pedal_conflict | 0 | 0% |
| stopped_shaft | 0 | 0% |
| any of them | 145 | 0.0248% |

No evaluation trips two rules.

Four of the eight compare two readings of one quantity or a fixed ratio between two.
The other four came from asking what else holds, and are the reason the layer reaches
past the moving truck.

| rule | what it asks | how often it fails on normal data |
|---|---|---|
| steering_sign | do the steering angle and the yaw rate point the same way | 6 of 35,715 above 0.02 rad/s |
| engine_off | with the engine at zero, are its six driven signals at zero | 0 of 97,237 |
| pedal_conflict | are both pedals pressed at once | 0 of 486,544 |
| stopped_shaft | with the wheels at zero, is the output shaft at zero | reads up to 31 rpm, limit at 50 |

steering_sign is the only check on VDC2. A size check on those signals does not work,
as the table above shows, but the direction does.

## Engine speed against the input shaft

An unbuilt rule. With the clutch closed the two should turn together and at p90 they
are within 2.9 rpm, but on 2.26% of rows they differ by up to 618 rpm, sustained, at
low speed in low gears. One case reads engine 1552 against input 934 with the
reported slip at 0.

ETC1 byte 1 holds the driveline and torque converter states that would explain it,
but it takes three values here, 204, 205 and 221, too few to place its bits. Until
they are placed 2.26% is two orders worse than the rules that exist.

## Signal pairs tested as rules

Each pair below is two ways of reading the same quantity, so a rule could check that
they agree. Whether that works depends on how far apart they drift on normal data,
against how far the quantity itself moves.

| pair | drift, p99 | the quantity's range | ratio |
|---|---|---|---|
| wheel_speed and tachograph_speed | 0.90 km/h | 90.10 | 1.0% |
| engine_load and actual_engine_torque | 10.0 points | 52.00 | 19.2% |
| lateral_accel and speed times yaw_rate | 0.69 m/s2 | 1.51 | 45.7% |
| accel_pedal and driver_demand_torque | 70.0 points | 92.80 | 75.4% |

The first drifts 0.90 km/h across a 90 km/h range, so a threshold just above the
drift still catches nearly any tampering. That pair is
[speed_agreement](../rules/instant/docs/speed_agreement.md). The last drifts 70 points out of
93, which leaves almost nothing for a threshold to catch, so no rule was written for
it, nor for the two in between.

Do not screen a pair by correlation. The last pair correlates at 0.803.

## Message checks not written

Four more checks are available. Every message type keeps a fixed period, a fixed
sender and a fixed byte count, and only 57 types appear at all, all measured above.

They would catch a different kind of attack, one that adds, drops or forges frames.
Nothing here synthesizes that yet, so there is nothing to measure them against and
none is written.
