# pgn_counts

Counts which message types are on the bus and which ECUs send them.

```python
count_pgns(frames)         # -> Counter of pgn -> frame count
count_pgn_senders(frames)  # -> {pgn: Counter of source address -> count}
```
