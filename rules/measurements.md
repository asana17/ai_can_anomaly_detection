# Rule measurements

What the rules in [instant](instant) and [rate](rate) were built on, and what was
measured and rejected. The dataset itself is in
[docs/measurements.md](../docs/measurements.md).

日本語版: [`measurements.ja.md`](measurements.ja.md)

## What the rules rest on

### How often the rules fire

Every rule in [rules](README.md) over 584,694 evaluations, one per decoded
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
| reverse_speed | 0 | 0% |
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

[change_limit](rate/docs/change_limit.md) is not in the table. It compares a
signal with its own previous reading rather than a whole state, so its evaluations
are not the same ones. Over 70 logs and 949,349 comparisons it fires twice.

### Nothing reads outside its range

Every decoded value is checked against the J1939 range `spn_spec` records for it.
Across 100 files that is 5,034,836 values over 17 signals, and none of them fall
outside. The rule layer's range check therefore starts from no false positives on
this data.

### How fast each signal moves

Between one frame of a message and the next of the same message, over 25 logs.

| signal | most per second | signal | most per second |
|---|---|---|---|
| yaw_rate | 1.1 rad/s2 | fuel_rate | 94.5 L/h |
| steering_angle | 16.4 rad/s | actual_engine_torque | 747.3 points |
| wheel_speed | 21.0 km/h | output_shaft_speed | 3,010 rpm |
| tachograph_speed | 41.9 km/h | engine_speed | 3,277 rpm |
| current_gear | 80 gears | clutch_slip | 3,790 points |
| selected_gear | 120 gears | input_shaft_speed | 75,235 rpm |

The four on the left of the first three rows are bounded by what a truck can do and
carry [change_limit](rate/docs/change_limit.md). The rest are not. A shift
frees the input shaft, the clutch slip follows it, and the gear number jumps several
places at once.

Sampling on the 100 ms grid gives lower figures for the fast signals, 1,951 rpm per
second for the engine against 3,277 here. A grid row spans 100 ms whatever arrived
inside it, so five engine updates fold into one difference. Limits measured one way
do not carry to the other.

## What did not become a rule

### Pairs that should have agreed

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
[speed_agreement](instant/docs/speed_agreement.md). The last drifts 70 points out of
93, which leaves almost nothing for a threshold to catch, so no rule was written for
it, nor for the two in between.

Do not screen a pair by correlation. The last pair correlates at 0.803.

### Other claims that did not hold

Five more shapes were tried. Each is a claim that normal data should never break.

| claim | how often normal data breaks it |
|---|---|
| reverse stays slow | never above 3.5 km/h in 87,245 |
| a running engine burns fuel | 6.4%, from coasting cuts |
| actual torque stays at or below demanded | 48.6% |
| actual torque stays at or below load | 1.4% |
| selected and current gear stay one step apart | up to 12 apart |

Only the first holds, and it is
[reverse_speed](instant/docs/reverse_speed.md). A rule built on any of the
others would fire on normal data at the rate in the second column.

### Why the input shaft is not checked

An unbuilt rule. With the clutch closed the two should turn together and at p90 they
are within 2.9 rpm, but on 2.26% of rows they differ by up to 618 rpm, sustained, at
low speed in low gears. One case reads engine 1552 against input 934 with the
reported slip at 0.

ETC1 byte 1 holds the driveline and torque converter states that would explain it,
but it takes three values here, 204, 205 and 221, too few to place its bits. Until
they are placed 2.26% is two orders worse than the rules that exist.

### Checks on the messages, not written

Four more checks are available. Every message type keeps a fixed period, a fixed
sender and a fixed byte count, and only 57 types appear at all, all measured above.

They would catch a different kind of attack, one that adds, drops or forges frames.
Nothing here synthesizes that yet, so there is nothing to measure them against and
none is written.
