# spn_spec

The SPN decode table: for each standard PGN we decode, the SPNs it carries and how
to decode each one. Data only; the decoding logic is in spn_decode.

## What it holds

`SPEC` maps a PGN to a list of `SpnDef`:

- `spn`, `name`, `unit` identify the signal.
- `field` is the `SpnField` geometry the decoder needs.
- `minimum` and `maximum` are the J1939 defined range. They verify decoding (real
  values must land in range) and later feed the rule layer range check.

## Scope

Fields the truck always sends as not available are omitted with a comment. A signal
that never arrives holds `ready()` False and stops every row. VDC2 byte 8 and SPN
184 are both that.

This table does not decide what the model reads.

## Verifying a layout

Positions are confirmed against the data before they go in. The
[FMS-Standard](https://www.fms-standard.com/Truck/down_load/fms%20document_v_05_vers.07.07.2024.pdf)
says what the interface can carry, not what this truck sends. It specifies a
longitudinal acceleration this truck never sends, and omits the yaw rate it sends
every 100 ms.
