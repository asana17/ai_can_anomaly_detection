# split

Cuts the logs by time, without shuffling, so later data never leaks into training.
`split` makes the train and test parts. `hold_out` takes the calibration set out of
the train one.

## Example

```python
weight = driving_time(logs)
train, test = split(logs, 0.75, weight)
train, calibration = hold_out(train, count, weight)
```

Logs are ordered by their filename, which is a timestamp. `split` cuts once, and
everything after the cut is the test set.

## Train and test are sized by seconds above 5 km/h

Only rows above `MIN_SPEED` are scored, and only they set the threshold. Everything
slower is left to the rules.

Cutting by log count can therefore leave a part with no scoreable rows. The truck is
parked for long runs of consecutive logs, so a part chosen by count alone can hold no
driving at all.

So the cut is made on the seconds above 5 km/h. `weight` is one number per log, and
`driving_time(logs)` sets it to the seconds that log spent above `MIN_SPEED`. A log
the truck sat still through gets a weight of 0, one it drove right through gets a
weight of about 60.

The fraction is taken over the sum of those weights, so `train_frac=0.75` gives train
75% of the driving.

`driving_time` reads every log, so the test period's driving affects where the cut
falls. Nothing from it reaches the fit.

## The calibration set

The rows that set the threshold must be ones the model never saw. `hold_out` keeps
`count` training logs aside as the calibration set, spaced out over the training
period, and the threshold is computed from the calibration rows.

| parameter | what it is |
|---|---|
| `count` | how many log files become the calibration set |
| `weight` | the seconds above 5 km/h each log holds, as in `split` |

[evaluate](../../evaluate) sets `count`.
