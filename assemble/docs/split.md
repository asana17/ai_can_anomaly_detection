# split

Splits the logs by time, without shuffling, so later data never leaks into
training.

## Example

```python
weight = driving_time(logs)
train, test = split(logs, 0.75, weight)
train, val = hold_out(train, 0.07, weight, blocks=5, gap=1)
```

Logs are ordered by their filename, which is a timestamp. `split` cuts once, and
everything after the cut is the test set.

## Size the parts in driving time, not in logs

The threshold comes from rows above `MIN_SPEED`, and cutting by log count can hand a
part none of them. The truck is parked in 581 of 1,200 logs and the parked runs are
long, so 111 of the 1,141 possible 60 log blocks hold no driving at all.

`driving_time` measures each log's seconds above `MIN_SPEED`. Passed as `weight` it
makes the fractions shares of driving time. It reads every log, so keep the result.

## Calibration comes out of the training period, in blocks

The threshold is read off normal rows the model never fitted, so it cannot come from
train itself. One contiguous block at the end of training will not do either. Over
1,200 logs such a block ran 15% higher in residual than test at every k, which moved
the false alarm rate by up to ten times.

`hold_out` takes several contiguous blocks spread across the period, and `gap` drops
the logs either side of each, since a log recorded a minute later is nearly the same
log. That is
[purged cross-validation](https://en.wikipedia.org/wiki/Purged_cross-validation) with
an embargo. The blocks stay contiguous because shuffling logs would put later traffic
next to earlier, which is what
[blocked splitting](https://robjhyndman.com/publications/cv-time-series/) exists to
prevent.
