# grid_sample

CAN frames arrive at uneven times, and each one carries only a few of the signals.
`resample` turns that messy stream into an even table: one row every fixed interval
(for example every 100 ms), with all signals filled in from their most recent
values. That regular table is the model's input.

## Example

```python
for t, vec in resample(frames, period=0.1):
    ...   # one row every 100 ms; vec holds all signals, in SIGNALS order
```

It outputs a row at each interval using the latest value of every signal. It waits
until all signals have been seen at least once, and between frames it holds the
last value, so every row is complete.

## Limits

- Arrival times are dropped (the rows are evenly spaced), so timing, flooding, or a
  silent signal cannot be seen from them. Those need the raw stream and rule checks.
- If the grid is finer than a signal's update rate, that signal repeats across rows,
  which a model reading time would take as real steadiness. At the default 100 ms
  grid this is minor, since the signals update about that often. It grows with a
  finer grid or when a signal stops.
