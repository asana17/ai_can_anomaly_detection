# split

Cuts the logs into train and test by time, without shuffling, so later data never
leaks into training.

## Example

```python
train, test = split(logs, 0.75, driving_time(logs))
```

Logs are ordered by their filename, which is a timestamp. `split` cuts once, and
everything after the cut is the test set.

## Size the parts in driving time, not in logs

Only rows above `MIN_SPEED` are scored, and only they set the threshold. Everything
slower is left to the rules.

Cutting by log count can therefore leave a part with no scoreable rows. The truck is
parked in 581 of 1,200 logs and the parked runs are long, so 111 of the 1,141
possible runs of 60 logs hold no driving at all.

So the cut is made on driving time. `weight` gives each log a size, and the fraction
is taken over the sum of those sizes instead of over the log count. `driving_time`
sets each size to the seconds that log spent above `MIN_SPEED`, so `train_frac=0.75`
gives train 75% of the driving.

`driving_time` runs over every log, so where the cut falls depends on the test period
as well. That changes how big each part is, not what the model learns from it.
