# spn_encode

Writes a physical value into a payload, the inverse of preprocess spn_decode.
Value-level attacks (spoof, masquerade) use it to overwrite a signal in a frame.

## What the code does

- `encode(value, field)` converts a physical value to the raw integer,
  `round((value - offset) / scale)`, clamped to the field width.
- `set_field(data, field, value)` returns a new payload with that field's bits
  replaced (little-endian), leaving the other bits unchanged.

Decoding the result returns the same value within one resolution step. That
reversibility is what value-level attack synthesis relies on.
