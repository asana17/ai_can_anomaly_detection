# spn_decode

Extracts one J1939 SPN field from a payload and returns its physical value.

```python
decode(data, field)              # -> physical value, or None if unavailable
extract_le(data, start_bit, n)   # -> raw unsigned integer
```

## Why decode

Decoding turns encoded bytes into physical numbers (rpm, km/h). It injects no
relationship between signals; the autoencoder still learns those from data. It
only cleans the input: one signal per dimension on a physical scale, with counter
and filler bytes dropped. A cleaner input needs a smaller model, which matters
because the device runs inference only and training is offline on a PC. The rule
layer reuses the same physical values for its range checks.
