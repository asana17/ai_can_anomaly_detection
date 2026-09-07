# split

Splits the log files into train, validation, and test by time, with no shuffling,
so later data never leaks into training.

## Example

```python
train, val, test = split(files, 0.70, 0.05)                        # 70 / 5 / 25 of the files
train, val, test = split(files, 0.70, 0.05, moving_frames(files))  # of the moving traffic
```

Files are ordered by their filename, which is a timestamp, then cut into three
chronological blocks.

## Size validation in moving traffic, not in files

The threshold comes from validation's moving rows. Cutting by file count can hand
validation a block with no moving row in it. The truck is parked in 581 of 1,200 logs
and the parked runs are long, so 111 of the 1,141 possible 60 log blocks hold no
moving frame at all.

`moving_frames` counts each log's readings above the gate. Passed as `weight` it
makes the fractions shares of moving traffic. It reads every log, so keep the counts.
