# spn_decode

Extracts one J1939 SPN field from a payload and returns its physical value.

```python
decode(data, field)              # -> physical value, or None if reserved
extract_le(data, start_bit, n)   # -> raw unsigned integer
```

## Reserved values

J1939 keeps the top of every field for indicators. A most significant byte of `0xFE`
means an error and `0xFF` means not available. Neither is a measurement, so `decode`
returns None and [frame_decode](frame_decode.md) leaves the signal out.

## Why decode

A signal's bits sit somewhere in a payload with a scale and offset of its own.
Decoding gives one number per signal on a physical scale, such as rpm for engine
speed and km/h for wheel speed. That is what makes values from different
PGNs comparable, and what the rule layer checks ranges against.
