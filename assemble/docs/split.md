# split

`split` cuts the logs into train and test. `split_rows` cuts the training rows into
train and calibration rows.

## Example

```python
weight = driving_time(logs)
train_logs, test_logs = split(logs, train_frac, weight)

raw, t, seg = grid_rows(train_logs)             # from train_set.md
train_rows, calibration_rows = split_rows(raw, t, share, block, gap)
```

## Train and test are sized by the seconds above the minimum speed

Only rows above `min_speed` are scored, and only they set the threshold. Everything
slower is left to the rules.

The truck is parked for long runs of consecutive logs, so a part chosen by log count
alone can hold no scoreable row at all.

So the cut is made on the seconds above `min_speed`. `weight` is one number per log,
and `driving_time(logs)` sets it to the seconds that log spent above it. The weight
is 0 for a log the truck sat still through, and the log's whole length for one it drove
right through.

## The calibration set

The rows that set the threshold must be ones the model never saw.

| argument | what it decides |
|---|---|
| `share` | how much of the seconds above `min_speed` calibrates |
| `block` | how long one calibration window is |
| `gap` | the seconds either side of a window that go to neither part |

So the windows fall `block / share` apart, and train is every row they and the gaps
leave.
