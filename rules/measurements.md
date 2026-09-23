# Rule measurements

What the rules in [instant](instant) and [rate](rate) were built on, and what was
measured and rejected. The dataset itself is in
[can_data/measurements.md](../can_data/measurements.md).

日本語版: [`measurements.ja.md`](measurements.ja.md)

## What the rules rest on

### How often the rules fire

Every rule in [rules](README.md) over 217,971,171 evaluations, one per decoded
frame of every log. The share is of all of them, so it is lower than the rate each
rule's own doc gives over the evaluations it applies to.

| rule | fires | share |
|---|---|---|
| range_check | 0 | 0% |
| speed_agreement | 37,941 | 0.0174% |
| shaft_ratio | 342 | 0.0002% |
| gear_ratio | 9,891 | 0.0045% |
| steering_sign | 7,105 | 0.0033% |
| engine_off | 141,110 | 0.0647% |
| pedal_conflict | 88,830 | 0.0408% |
| stopped_shaft | 2,600 | 0.0012% |
| reverse_speed | 297 | 0.0001% |
| reserved_moving | 0 | 0% |
| any of them | 282,896 | 0.1298% |

5,003 evaluations trip two rules or more.

### On the rows the evaluation reads

The evaluation reads the moving grid rows, 2,757,787 of them over every log. There
the rules together fire on 2,090, 0.0758%, under the 0.1% the models' thresholds cut
off. Two limits were set to get there.

| rule | before | after |
|---|---|---|
| steering_sign, MIN_YAW 0.02 to 0.05 | 2,545 | 191 |
| shaft_ratio, from 5 km/h to 20 km/h | 1,176 | 15 |
| any of them | 5,472 | 2,090 |

The rest fire on pedal_conflict 1,066, speed_agreement 587, gear_ratio 317,
reverse_speed 9 and none of the others.

Besides range_check, four rules compare two readings of one quantity or a fixed ratio
between two. Four more came from asking what else holds, and are the reason the layer
reaches past the moving truck. reserved_moving flags a reserved value on the move,
which no other rule judges.

Over every log, one evaluation per decoded frame.

| rule | what it asks | how often it fails on normal data |
|---|---|---|
| steering_sign | do the steering angle and the yaw rate point the same way | 85,134 of 28,095,820 above 5 km/h and 0.02 rad/s |
| engine_off | with the engine at zero, are its six driven signals at zero | 141,110 of 36,041,922 |
| pedal_conflict | are both pedals pressed at once | 88,830 of 216,709,675 |
| stopped_shaft | with the wheels at zero, is the output shaft at zero | reads up to 551 rpm, limit at 50, 2,600 of 106,072,217 above it |

steering_sign is the only check on VDC2. A size check on those signals does not work,
as the table above shows, but the direction does.

[change_limit](rate/docs/change_limit.md) is not in the table. It compares a
signal with its own previous reading rather than a whole state, so its evaluations
are not the same ones. Over every log and 85,944,337 comparisons it fires 236 times,
149 on yaw_rate, 44 on tachograph_speed and 43 on wheel_speed.

### Nothing reads outside its range

Every decoded value is checked against the J1939 range `spn_spec` records for it.
Across every log that is 565,906,098 values over 17 signals, and none of them fall
outside. The rule layer's range check therefore starts from no false positives on
this data.

### How fast each signal moves

Between one frame of a PGN and the next of the same PGN, over every log.

| signal | most per second | signal | most per second |
|---|---|---|---|
| yaw_rate | 5.6 rad/s2 | fuel_rate | 470.7 L/h |
| steering_angle | 36.3 rad/s | actual_engine_torque | 2,731.3 points |
| wheel_speed | 374.8 km/h | output_shaft_speed | 54,891 rpm |
| tachograph_speed | 745.0 km/h | engine_speed | 7,843 rpm |
| current_gear | 120 gears | clutch_slip | 25,980 points |
| selected_gear | 122 gears | input_shaft_speed | 671,757 rpm |

The four on the left of the first three rows carry
[change_limit](rate/docs/change_limit.md). Its limits came from 25 logs. Over every
log all of them but steering_angle move faster than their limit, which is where its
236 hits come from. The rest carry no limit. A shift
frees the input shaft, the clutch slip follows it, and the gear number jumps several
places at once.

Sampling on the 100 ms grid gives lower figures for the fast signals, 3,464 rpm per
second for the engine against 7,843 here. A grid row spans 100 ms whatever arrived
inside it, so five engine updates fold into one difference. Limits measured one way
do not carry to the other.

## What did not become a rule

### Pairs that should have agreed

Each pair below is two ways of reading the same quantity, so a rule could check that
they agree. Whether that works depends on how far apart they drift on normal data,
against how far the quantity itself moves.

Over every log, on the evaluations above 5 km/h. The drift is the p99 of the
difference between the two, and the range is the p99 of the first one's size.

| pair | drift, p99 | the quantity's range | ratio |
|---|---|---|---|
| wheel_speed and tachograph_speed | 0.91 km/h | 85.51 | 1.1% |
| engine_load and actual_engine_torque | 12.0 points | 87.01 | 13.8% |
| lateral_accel and speed times yaw_rate | 0.85 m/s2 | 1.33 | 63.9% |
| accel_pedal and driver_demand_torque | 30.4 points | 85.21 | 35.7% |

The first drifts 0.91 km/h across an 86 km/h range, so a threshold just above the
drift still catches nearly any tampering. That pair is
[speed_agreement](instant/docs/speed_agreement.md). The other three drift 14% to 64%
of their range, which leaves little for a threshold to catch, so no rule was written
for them.

Do not screen a pair by correlation. The last pair correlates at 0.924.

### Other claims that did not hold

Five more shapes were tried. Each is a claim that normal data should never break.
Over every log, one evaluation per decoded frame, the torque and fuel claims on those
with the engine running.

| claim | how often normal data breaks it |
|---|---|
| reverse stays slow | up to 38.3 km/h in 26,197,193 |
| a running engine burns fuel | 9.8%, from coasting cuts |
| actual torque stays at or below demanded | 48.0% |
| actual torque stays at or below load | 1.8% |
| selected and current gear stay one step apart | up to 12 apart |

None holds over every log.
[reverse_speed](instant/docs/reverse_speed.md) was built on the first when 87,245
evaluations never passed 3.5 km/h, and now fires 297 times.

### Why the input shaft is not checked

An unbuilt rule. With the clutch closed the two should turn together. Over every log,
on the evaluations above 5 km/h with a slip of 0, they are within 3.9 rpm at p90, but
on 4.21% they differ by more than 50 rpm, up to 1,518 rpm. One case reads engine 1552
against input 934 with the reported slip at 0.

ETC1 byte 1 holds the driveline and torque converter states that would explain it,
but it takes three values here, 204, 205 and 221, too few to place its bits. Until
they are placed 4.21% is two orders worse than the rules that exist.

### Checks on the PGNs, not written

Four more checks are available. Every PGN keeps a fixed period, a fixed
sender and a fixed byte count, and only 57 types appear at all, all measured above.

They would catch a different kind of attack, one that adds, drops or forges frames.
Nothing here synthesizes that yet, so there is nothing to measure them against and
none is written.
