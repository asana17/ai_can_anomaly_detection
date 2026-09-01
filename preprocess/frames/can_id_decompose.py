"""Decompose a 29-bit J1939 arbitration ID into (priority, PGN, source address)."""

from typing import NamedTuple

_EXTENDED_ID_MASK = 0x1FFFFFFF
_PDU1_FORMAT_LIMIT = 240   # PF < 240 is PDU1 (destination-specific), else PDU2


class CanId(NamedTuple):
    priority: int
    pgn: int
    source_address: int


def decompose_can_id(arb_id: int) -> CanId:
    """Return the priority, PGN, and source address encoded in a 29-bit CAN ID."""
    ident = arb_id & _EXTENDED_ID_MASK

    source_address = ident & 0xFF
    pdu_specific = (ident >> 8) & 0xFF
    pdu_format = (ident >> 16) & 0xFF
    data_page = (ident >> 24) & 0x1
    priority = (ident >> 26) & 0x7

    if pdu_format < _PDU1_FORMAT_LIMIT:
        # PDU1: PDU Specific is a destination address, excluded from the PGN.
        pgn = (data_page << 16) | (pdu_format << 8)
    else:
        pgn = (data_page << 16) | (pdu_format << 8) | pdu_specific

    return CanId(priority=priority, pgn=pgn, source_address=source_address)
