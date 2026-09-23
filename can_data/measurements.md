# Measurements

What profiling the logs found. The dataset itself is described in
[can_data](can_data.md). The per PGN figures come from
[summary](../preprocess/docs/summary.md), which reruns them on any set of logs.

日本語版: [`measurements.ja.md`](measurements.ja.md)

## The bus and the truck

### What is on the bus

Over every log, 11,194 of them, and 559,711,194 frames.

- **57 unique PGNs.** One log carries 52 to 57 of them (median 55), and 52 appear
  in every log. **10 source addresses**, of which `230`, the main powertrain ECU,
  sends 75.9% of all frames. The next five send 3.5 to 3.9% each.
- DLC distribution: `8` is **98.22%**, then `4` 1.19%, `1` 0.59%, `3` under 0.01%.
- **41 PGNs are public and 16 are proprietary**, carrying 76.1% and 23.9% of frames.
  The proprietary ones have no published SPN definitions, so they cannot be decoded.
  See [pgn_classify](../preprocess/docs/pgn_classify.md).
- **EEC1, EEC2, CCVS1 and LFE1 are in 100% of logs** (share of frames, rate):
  - `EEC1` (61444), 5.91%, every 20 ms, engine speed and engine torque
  - `EEC2` (61443), 2.36%, every 50 ms, accelerator pedal and engine percent load
  - `CCVS1` (65265), 1.18%, every 100 ms, wheel based vehicle speed
  - `LFE1` (65266), 1.18%, every 100 ms, engine fuel rate
- `ETC2` (61445) is in every log at 10 Hz, carrying SPN 524 selected gear and SPN
  523 current gear. Observed values are `-2` and `-1` reverse, `0` neutral and `1`
  to `12`, with `0xFF` not available in 0.44% of frames. `-2` comes in about 500
  frames.
- **Multi packet transport is small and always present.** TP.CM (60416) is 0.25% of
  frames and TP.DT (60160) is 0.74%. Neither carries the target SPNs.

Rates are the median gap per (PGN, source address) stream, not frames divided by
log duration. The latter understates any log that contains a gap.

### The nine decoded PGNs

Over every log, 11,194 of them, holding 218,251,623 frames of the nine PGNs this
repo decodes.

- **One source address.** Every one of those frames comes from `230`. No other
  address sends the nine, so a slot per PGN holds what a slot per CAN ID would, which
  is what [signal_state](../preprocess/docs/signal_state.md) keeps.
- **Reserved values arrive only while the truck stands.** Not one comes while the
  wheel speed before it is above 5 km/h. `steering_angle` has the most at 398,974
  frames and `brake_pedal` the fewest at 1,947. Only `clutch_slip` (16,721) and
  `input_shaft_speed` (3,509) ever send the `0xFE` error. The rows the model and the
  rules see are therefore untouched by how a reserved value is read.

### The gearbox

A 12 speed box. Grouping the gridded rows by current gear, engine speed over wheel
speed lands on one ratio per gear.

| gear | 12 | 11 | 10 | 9 | 8 | 7 | 6 | 5 | 4 |
|---|---|---|---|---|---|---|---|---|---|
| rpm per km/h | 15.25 | 19.43 | 24.87 | 31.71 | 41.21 | 52.37 | 66.51 | 84.73 | 108.51 |

Each step is 1.26 to 1.30, and the same ratios appear in all four parts, which is
what one fixed gearbox should give. The gear reported in ETC2 matches these to
within 0.3% for gears 4 to 12. In 0.5 rpm per km/h bins the histogram between two
of these ratios falls to 0.6% to 4.4% of the smaller peak, so a pair of engine and
wheel speeds either sits on a gear or is rare. Below fourth the peaks overlap more,
10% between third and fourth and 51% between first and second.

Top gear at 15.25 matches the ETC1 output shaft, which also turns at 15.25 rpm per
km/h, so twelfth is direct.

### Three of the decoded signals are one quantity

While moving, wheel_speed, output_shaft_speed and tachograph_speed correlate at
0.9999 or above. Over 2,757,787 moving rows the 17 signals have an effective rank
of 15, and the two smallest principal directions hold 2.8e-06 and 4.6e-07 of the
variance.

They stay decoded because a replay of one leaves the others alone, which is what
[speed_agreement](../rules/instant/docs/speed_agreement.md) and
[shaft_ratio](../rules/instant/docs/shaft_ratio.md) test. A model reading all three
sees fewer free directions than its 17 columns suggest.

### How much of the time the truck drives

Over every log the grid yields 6,608,250 rows.

| state | share |
|---|---|
| engine off | 16.5% |
| engine on, at or below 5 km/h | 41.7% |
| above 5 km/h | 41.7% |

Gear coverage is far from even. Of the 2,757,787 rows above 5 km/h, top gear holds
829,206 and first gear 14,097, a spread of 59 to 1. A model trained on this sees the
low gears rarely.

### Gaps between frames

Of 559,700,000 consecutive frame gaps, 77.05% fall under 1 ms and 22.95% between 1
and 10 ms. Only 202 land between 10 and 100 ms, and the longest of those is 60 ms.
Six land between 100 ms and 2 seconds, at 0.89, 1.01, 1.17, 1.39, 1.57 and 1.92
seconds. 450 gaps in 219 logs exceed 2 seconds, and those are the recording breaks.

**None at all fall between 60 ms and 0.89 seconds.** A threshold placed in that
band separates the same 456 gaps from normal traffic. This is what
[grid_sample](../preprocess/docs/grid_sample.md) uses `max_hold` for. The 1 second
this repo passes lies above that band, among the six, so five of them count as
breaks and the one at 0.89 does not.
