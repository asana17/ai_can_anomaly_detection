# grid_sample

CAN frames arrive at uneven times, and each one carries only a few of the signals.
`resample` turns that messy stream into an even table: one row every fixed period
(for example every 100 ms), with all signals filled in from their most recent
values. That regular table is the model's input.

## Example

```python
for t, vec in resample(frames, period=0.1, max_hold=1.0):
    ...   # one row every 100 ms; vec holds all signals, in SIGNALS order
```

It outputs a row at each tick using the latest value of every signal. It waits
until all signals have been seen, and between frames it holds the last value, so
every row is complete.

`max_hold` is how long a value may be held. A gap longer than that means the
recording stopped, not that the signals held steady, so `resample` emits no rows
across the gap, restarts the grid from the first frame after, and drops the values
from before it. Rows resume once every signal has arrived again.

Dropping the old values matters as much as skipping the gap. One carried across
would sit in its normal range while no longer agreeing with the fresh signals
beside it, which is the fault the model is trained to catch.

Gaps that large are real. One log in this dataset holds a 70.6 hour one, which
without `max_hold` becomes 2,547,687 invented rows. The whole distribution is in
[measurements](../../docs/measurements.md).

Both defaults come from the dataset rather than from the module. `period` is 100 ms
because that is how often the slowest target PGNs (CCVS1, LFE1) arrive, and a
shorter period only repeats their last value across rows. `max_hold` is 1 second,
ten of those arrivals.

## Limits

- Arrival times are dropped (the rows are evenly spaced), so timing, flooding, or a
  silent signal cannot be seen from them. Those need the raw stream and rule checks.
- If the period is shorter than a signal's update rate, that signal repeats across
  rows, which a model reading time would take as real steadiness. At the default
  100 ms period this is minor, since the signals update about that often. It grows
  with a shorter period, and `max_hold` bounds how far it can go.
