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
| engine_off | 1,836 | 0.0008% |
| pedal_conflict | 58,420 | 0.0268% |
| stopped_shaft | 110 | 0.0001% |
| reverse_speed | 297 | 0.0001% |
| reserved_moving | 0 | 0% |
| any of them | 113,201 | 0.0519% |

2,579 evaluations trip two rules or more.

### On the rows the evaluation reads

The evaluation reads the moving grid rows, 2,757,787 of them over every log. There
the rules together fire on 1,645, 0.0596%, under the 0.1% the models' thresholds cut
off. Three limits were set to get there.

| rule | before | after |
|---|---|---|
| steering_sign, MIN_YAW 0.02 to 0.05 | 2,545 | 191 |
| shaft_ratio, from 5 km/h to 20 km/h | 1,176 | 15 |
| pedal_conflict, PRESSED 1% to 10% | 1,066 | 620 |
| any of them | 5,472 | 1,645 |

The rest fire on speed_agreement 587, gear_ratio 317, reverse_speed 9 and none of the
others. On test_sets/20260924-064408 the rules alone catch 483 of 1,089 attacks at a
hold of 10 rows with 0.29 false alarms an hour, against 543 and 1.84 before the three
changes.

engine_off leaves out the input shaft and stopped_shaft needs the tachograph at zero
too. Neither fires on a moving row, before or after. The change is to the stopped
evaluations, 141,110 to 1,836 and 2,600 to 110.

Besides range_check, four rules compare two readings of one quantity or a fixed ratio
between two. Four more came from asking what else holds, and are the reason the layer
reaches past the moving truck. reserved_moving flags a reserved value on the move,
which no other rule judges.

Over every log, one evaluation per decoded frame.

| rule | what it asks | how often it fails on normal data |
|---|---|---|
| steering_sign | do the steering angle and the yaw rate point the same way | 85,134 of 28,095,820 above 5 km/h and 0.02 rad/s |
| engine_off | with the engine at zero, are its five driven signals at zero | 1,836 of 36,041,922 |
| pedal_conflict | are both pedals pressed at once, above 10% | 58,420 of 216,709,675 |
| stopped_shaft | with both speeds at zero, is the output shaft at zero | limit at 50 rpm, 110 of the evaluations above it |

steering_sign is the only check on VDC2. A size check on those signals does not work,
as the table above shows, but the direction does.

[change_limit](rate/docs/change_limit.md) is not in the table. It compares a row
with the row before it rather than reading one row. On the moving rows it fires on
87, 68 of them rows no instant rule fires on. With it the rules fire on 1,713,
0.0621%.

### Nothing reads outside its range

Every decoded value is checked against the J1939 range `spn_spec` records for it.
Across every log that is 565,906,098 values over 17 signals, and none of them fall
outside. The rule layer's range check therefore starts from no false positives on
this data.

### How fast each signal moves

Between a moving grid row and the row before it, one tick earlier in the same
segment and moving too. 2,749,873 steps over every log, per second.

| signal | 1e-4 | 1e-5 | most |
|---|---|---|---|
| engine_speed | 2,114 rpm | 2,509 | 2,825 |
| driver_demand_torque | 350 % | 610 | 930 |
| actual_engine_torque | 250 % | 360 | 490 |
| accel_pedal | 340 % | 642 | 1,000 |
| engine_load | 360 % | 530 | 730 |
| wheel_speed | 21.0 km/h | 37.0 | 317 |
| fuel_rate | 186 L/h | 305 | 471 |
| output_shaft_speed | 320 rpm | 500 | 4,850 |
| clutch_slip | 460 % | 980 | 1,000 |
| input_shaft_speed | 8,120 rpm | 10,590 | 14,160 |
| selected_gear | 120 gears | 120 | 120 |
| current_gear | 80 gears | 100 | 110 |
| tachograph_speed | 21.0 km/h | 33.0 | 317 |
| brake_pedal | 144 % | 212 | 360 |
| steering_angle | 7.38 rad/s | 9.39 | 11.1 |
| yaw_rate | 0.283 rad/s2 | 0.364 | 0.488 |
| lateral_accel | 20.4 m/s2 | 28.9 | 46.0 |

[change_limit](rate/docs/change_limit.md) limits seven of them, each just above its
1e-5 figure. At 1e-4 the seven would fire on 1,693 rows and take the rules to 3,118,
over 0.1%. accel_pedal and clutch_slip move their whole range in one row and the gear
number jumps several places. A shift frees the input shaft.

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

The first drifts 0.91 km/h across an 86 km/h range, so a threshold just above the
drift still catches nearly any tampering. That pair is
[speed_agreement](instant/docs/speed_agreement.md).

engine_load is a share of the most torque at the present speed, so it sits at or above
actual_engine_torque. Torque above load stays within 2 points on 99% of moving grid rows.

lateral_accel also carries gravity from a banked road and body roll, an offset that
averaging keeps, still 47% of the range over 50 rows. No rule checks that pair.

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
but over every log it takes four values, 204, 205, 220 and 221, and 0xFF, too few to
place its bits. Until
they are placed 4.21% is two orders worse than the rules that exist.

### Checks on the PGNs, not written

Four more checks are available. Every PGN keeps a fixed period, a fixed
sender and a fixed byte count, and only 57 types appear at all, all measured above.

They would catch a different kind of attack, one that adds, drops or forges frames.
Nothing here synthesizes that yet, so there is nothing to measure them against and
none is written.
