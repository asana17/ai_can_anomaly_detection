# split

Splits the log files into train, validation, and test by time, with no shuffling,
so later data never leaks into training.

## Example

```python
train, val, test = split(files, 0.70, 0.05)   # 70 / 5 / 25
train, val, test = split(files, 0.80, 0.10)   # 80 / 10 / 10
```

Files are ordered by their filename, which is a timestamp, then cut into three
chronological blocks.
