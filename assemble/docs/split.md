# split

Cuts the logs by time, without shuffling, so later data never leaks into training.
`split` makes the train and test parts. `hold_out` takes the calibration set out of
the train one.

## Example

```python
weight = driving_time(logs)
train, test = split(logs, 0.75, weight)
train, calibration = hold_out(train, frac, weight, blocks, gap)
```

Logs are ordered by their filename, which is a timestamp. `split` cuts once, and
everything after the cut is the test set.

## Train, calibration and test are sized by seconds above 5 km/h

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
some training logs aside as the calibration set, and the threshold is computed from
the calibration rows.

The calibration logs are taken in blocks, from several places in the recording.
Taking them from one place would set the threshold on the driving of that part alone.

The logs on each side of a calibration block are dropped. They would otherwise be
training logs. A hard brake or a sharp turn lasts a few seconds and can run
across a log boundary. Without the drop, the same event would be in the fit and in
the rows the threshold comes from.

The calibration set is the same whatever `gap` is. Only the training set shrinks. How
much this matters is unmeasured, and for PCA it should be nothing, since a subspace
fitted on hundreds of thousands of rows cannot hold one event.

| parameter | what it is |
|---|---|
| `frac` | how much of the training driving time becomes calibration, 0 to 1 |
| `blocks` | how many blocks the calibration logs are taken in |
| `gap` | logs dropped on each side of a calibration block, a count not a time |

[evaluate](../../evaluate) sets all three.

The calibration set comes out a little smaller than `frac` asks for, because a block
stops at a whole log.
