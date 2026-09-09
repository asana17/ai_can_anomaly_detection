# Measurements

What profiling the logs found. The dataset itself is described in
[can_data](can_data.md). The per PGN figures come from
[summary](../preprocess/docs/summary.md), which reruns them on any set of logs.

日本語版: [`measurements.ja.md`](measurements.ja.md)

## The bus and the truck

### What is on the bus

Over 1,200 logs and 60,001,200 frames.

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
  523 current gear. Observed values are `-1` reverse, `0` neutral and `1` to `12`,
  with `0xFF` not available in 0.68% of frames.
- **Multi packet transport is small and always present.** TP.CM (60416) is 0.25% of
  frames and TP.DT (60160) is 0.74%. Neither carries the target SPNs.

Rates are the median gap per (PGN, source address) stream, not frames divided by
log duration. The latter understates any log that contains a gap.

### The gearbox

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

### Three of the decoded signals are one quantity

While moving, wheel_speed, output_shaft_speed and tachograph_speed correlate at
0.9999 or above. Over 200,644 moving rows the 17 signals have an effective rank of
15, and the two smallest principal directions hold 3.1e-06 and 5.2e-07 of the
variance.

They stay decoded because a replay of one leaves the others alone, which is what
[speed_agreement](../rules/instant/docs/speed_agreement.md) and
[shaft_ratio](../rules/instant/docs/shaft_ratio.md) test. A model reading all three
sees fewer free directions than its 17 columns suggest.

### How much of the time the truck drives

Over 1,200 logs the grid yields 704,493 rows.

| state | share |
|---|---|
| engine off | 16.3% |
| idling, engine on and stopped | 32.2% |
| moving | 51.5% |

Gear coverage is far from even. Of 251,894 steady moving rows, top gear holds 48,078
and the low gears around 1,000 each, a spread of about 44 to 1. A model trained on
this sees the low gears rarely, so results should be read per gear rather than
pooled.

### Gaps between frames

Of 60,000,000 consecutive frame gaps, 76.9% fall under 1 ms and 23.1% between 1 and
10 ms. Only 27 land between 10 and 100 ms, and **none at all between 100 ms and
2 seconds**. Sixty gaps exceed 2 seconds, and those are the recording breaks.

The distribution is empty over more than a decade, so any threshold placed in that
band separates the same 60 breaks from normal traffic. This is what
[grid_sample](../preprocess/docs/grid_sample.md) uses `max_hold` for, and why its
value is not delicate.
