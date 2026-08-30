# spn_decode

Extracts one J1939 SPN field from a payload and returns its physical value.

## What the code does

- `SpnField(start_bit, length, scale, offset)` describes where a signal sits in
  the payload and how to scale it. It carries geometry only, no name or PGN.
- `extract_le(data, start_bit, length)` reads the raw unsigned integer using
  J1939 little-endian (Intel) bit order.
- `decode(data, field)` returns `raw * scale + offset` as a float, or `None` when
  every bit of the field is set, which J1939 uses for "not available".

It decodes a single field. Naming fields and grouping them into a vector are other
steps.

## Why decode

Decoding turns encoded bytes into physical numbers (rpm, km/h). It injects no
relationship between signals; the autoencoder still learns those from data. It
only cleans the input: one signal per dimension on a physical scale, with counter
and filler bytes dropped. A cleaner input needs a smaller model, which matters
because the device runs inference only and training is offline on a PC. The rule
layer reuses the same physical values for its range checks.
