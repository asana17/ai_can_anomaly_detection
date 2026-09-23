# reserved_moving

Flags a reserved value, not available or an error, while the truck moves.

```python
hits(raw)   # -> True per row the rule fires on
```

A reserved value decodes to NaN. The other rules and the model do not judge a NaN,
so without this one a frame forged to carry 0xFF or 0xFE would pass unseen.

Over every log a reserved value only arrives with both vehicle speeds at 0. Either
speed above 0 counts as moving, so a reserved value put in one of them is still
caught by the other.
