# pgn_classify

Flags whether a PGN is manufacturer-proprietary.

## Why

Standard J1939 PGNs have public SPN definitions, so their payloads decode to
physical values. Proprietary PGNs have none, so they cannot be decoded without the
vendor database. Classifying the PGNs tells us which ones can be SPN-decoded.

## What the code does

`is_proprietary_pgn(pgn)` returns True for the J1939 proprietary groups:
Proprietary B (PDU Format 255) and Proprietary A / A2 (PGN 61184 / 126720). The
check is structural. A standard result means decodable in principle; the SPN bit
definitions still come from a J1939 reference.
