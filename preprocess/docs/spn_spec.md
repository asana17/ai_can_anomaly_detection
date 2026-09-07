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

## What is left out

Eleven FMS PGNs on this bus are not decoded. TD (65254) is a clock. The other ten
were decoded and measured first.

| PGN | signal | R2 |
|---|---|---|
| 65263 EFL/P1 | engine oil pressure | 0.51 |
| 65198 AIR1 | brake air pressure 1 and 2 | 0.15 |
| 65269 AMB | ambient air temperature | 0.08 |
| 64777 HRLFC | trip fuel | 0.08 |
| 65217 VDHR | total distance | 0.08 |
| 65253 HOURS | engine hours | 0.08 |
| 65262 ET1 | coolant temperature | 0.07 |
| 65272 TRF1 | transmission oil temperature | 0.07 |
| 65110 AT1T1I | diesel exhaust fluid level | 0.07 |
| 65276 DD | fuel level | 0.05 |

R2 is how well the seventeen signals already in predict each one, over 236,468 moving
rows. The weakest signal already in reaches 0.29. A signal the others cannot predict
holds no relation to break, so it widens the residual without adding anything to
check.

The three counters carry a second problem.

- A chronological split puts every test level beyond every training one, so only a
  difference is available.
- They arrive at 1 Hz, so that difference is zero in nine rows of ten.
- Over one second it gives the speed to within 16 km/h, where CCVS1 carries 0.004.

Their sender is not the one CCVS1 comes from, so a replay of the speed leaves them
alone. That makes a rate rule, not a signal here.

HRLFC does not carry what the standard says. SPN 5054 in bytes 1 to 4 is always not
available, and bytes 5 to 8 hold a trip counter instead.

## Verifying a layout

Positions are confirmed against the data before they go in. The
[FMS-Standard](https://www.fms-standard.com/Truck/down_load/fms%20document_v_05_vers.07.07.2024.pdf)
says what the interface can carry, not what this truck sends. It specifies a
longitudinal acceleration this truck never sends, and omits the yaw rate it sends
every 100 ms.
