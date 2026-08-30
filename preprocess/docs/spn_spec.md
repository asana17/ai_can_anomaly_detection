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

Starts with the powertrain PGNs (EEC1, EEC2, CCVS1, LFE1), verified against real
data. More standard PGNs are added over time. Which signals finally feed the model
is decided later from data, not fixed here.
