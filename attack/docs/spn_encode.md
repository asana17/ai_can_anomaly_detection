# spn_encode

Writes a physical value into a payload, the inverse of preprocess spn_decode.
Value-level attacks (spoof, masquerade) use it to overwrite a signal in a frame.

```python
set_field(data, field, value)   # -> new payload with that signal overwritten
encode(value, field)            # -> raw integer for the field
```

Decoding the result returns the same value within one resolution step. That
reversibility is what value-level attack synthesis relies on.
