# frame_decode

Decodes all known SPNs of one frame into named physical values.

## What the code does

`decode_frame(pgn, data)` looks up the PGN in the spn_spec table and decodes each
of its SPNs with spn_decode. It returns a `{name: value}` dict of physical values.

- SPNs that read as unavailable (all 0xFF) are omitted from the dict.
- A PGN with no entry in the table returns an empty dict.
