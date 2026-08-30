# can_id_decompose

Extracts the routing fields the pipeline needs from a raw 29-bit J1939
arbitration ID. `decompose_can_id(arb_id)` returns
`CanId(priority, pgn, source_address)`.

## What the code does

The 29-bit identifier packs several J1939 fields. The function reads the ones we
need by shifting and masking.

```
bits 28..26  Priority   arbitration priority
bit  24      DP         data page (selects the PGN number range)
bits 23..16  PF         PDU Format
bits 15..8   PS         PDU Specific
bits  7..0   SA         source address (which ECU sent the frame)
```

Bit 25 (EDP) is 0 for standard J1939 and is not used here.

### Assembling the PGN

The PGN (the message type) is not stored as one field. The code builds it from
DP, PF, and sometimes PS, choosing by the PF value.

- When `PF < 240` the frame is addressed to one ECU, so PS is a destination
  address and is left out of the PGN.
  `pgn = (DP << 16) | (PF << 8)`
- When `PF >= 240` the frame is a broadcast, so PS is part of the PGN.
  `pgn = (DP << 16) | (PF << 8) | PS`

Worked example for `0x18F004E6`. PF is `0xF0` (240), so PS is folded in.
`pgn = (240 << 8) | 4 = 61444`, which is EEC1 (engine control). SA is `0xE6`
(230) and priority is 6.

### Masking the high bits

`arb_id` is masked to its low 29 bits before decoding. Capture formats often
carry CAN flags (extended, remote, error) in bits 29 to 31, which are not part
of the identifier. Masking strips them so a flagged value still decodes. For the
clean IDs in this dataset the mask changes nothing.

## Why all three fields are returned

Decoding the payload needs only the PGN, but the anomaly checks downstream use
the other two as well.

- `source_address` flags spoofing, a known PGN arriving from an unexpected ECU.
- `priority` helps flag flooding, a burst of high-priority IDs.

Full field definitions are in the SAE J1939 standard.
