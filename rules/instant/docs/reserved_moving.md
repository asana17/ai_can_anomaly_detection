# reserved_moving

Flags a reserved value, not available or an error, while the truck moves.

```python
hits(raw)   # -> True per row the rule fires on
```

A reserved value decodes to NaN. The other rules and the model do not judge a NaN,
so without this one a frame forged to carry 0xFF or 0xFE would pass unseen.

Over every log a reserved value only arrives with both vehicle speeds and the output
shaft at 0, and the rule fires on none of 217,971,171 evaluations, one per decoded
frame. Any of the three above 0 counts as moving.
They come from CCVS1, TCO1 and ETC1, so a reserved value put in one or two of them is
still caught by the rest.
