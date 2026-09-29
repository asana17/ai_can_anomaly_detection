# settings

`common/settings.py` holds every value a run is made with, one class for each stage
that reads any, and the folders and repos the pipeline passes to them. A stage sees its own class alone, and a value an earlier stage fixed
comes from that stage's `meta.json`. This says how the ones below were set. None of
them was chosen by looking at the test set.

A run with other values gives the [pipeline](../../pipeline/README.md) a JSON file
with an object for each stage it changes, such as `{"split_test_logs": {"FOLD": 0}}`.
The values a stage used are in its `meta.json`.

## The split and calibration parameters

| stage | name | value | what it is |
|---|---|---|---|
| `split_test_logs` | `MIN_SPEED` | 5.0 km/h | the speed a row has to exceed to be scored |
| `calibrate` | `ROW_TARGET` | 1.5 | the false alarms an hour the alarm on every tick may raise on the calibration rows |
| `calibrate` | `ROW_K` | 10 | the k of the last N that alarm is held to `ROW_TARGET` at |
| `calibrate` | `WINDOW_TARGET` | 0.5 | the false alarms an hour a window model's alarm may raise on the calibration windows |
| `calibration_set` | `CALIBRATION` | 0.10 | the share of the training seconds above 5 km/h that become the calibration set |
| `calibration_set` | `BLOCK` | 20 s | the seconds above 5 km/h in one calibration block |
| `calibration_set` | `GAP` | 5 s | the time between a calibration block and the test span where rows are dropped |
| `train_set` | `GAP` | 5 s | the time either side of a calibration block or the test span where train rows are dropped |

- **`ROW_TARGET`** and **`WINDOW_TARGET`** are the false alarms an hour the thresholds
  aim at. They share out one budget. The evaluation joins the alarm on every tick and
  a window model's with OR, and counts alarm stretches that overlap as one. So the two
  together can raise fewer than the sum. The rows take the larger share, as they catch most attacks, and the rules'
  own false alarms count against it. Raising either lowers its thresholds, which
  catches more attacks and raises more false alarms. A stated choice, not a
  calculation.
- **`CALIBRATION`** has to leave enough calibration hours for the targets to rest on
  more than a few alarms. At about 5.7 moving hours, `ROW_TARGET` allows 8 alarms and
  `WINDOW_TARGET` 2. Raising it takes rows off the fit. A stated choice, not a
  calculation.
- **`BLOCK`** sets how many separate situations `CALIBRATION` buys. The truck's
  situation changes over about 20 seconds, so a window that long holds about one of
  them. A stated choice, not a calculation.
- **`GAP`** only has to cover the event it keeps out of both parts, which is seconds
  for a hard brake. Each of the two stages keeps its own, and neither needs the other's. Every one of them costs training rows, so it stays well under
  `BLOCK`.
