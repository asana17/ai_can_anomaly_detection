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

Decoding turns encoded bytes into physical numbers (rpm, km/h). It injects no
relationship between signals; the autoencoder still learns those from data. It
only cleans the input: one signal per dimension on a physical scale, with counter
and filler bytes dropped. A cleaner input needs a smaller model, which matters
because the device runs inference only and training is offline on a PC. The rule
layer reuses the same physical values for its range checks.
