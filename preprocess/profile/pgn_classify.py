"""Flag whether a PGN is manufacturer-proprietary (no public SPN definitions)."""


def is_proprietary_pgn(pgn: int) -> bool:
    if (pgn >> 8) & 0xFF == 0xFF:      # Proprietary B (PDU Format 255)
        return True
    return pgn in (0xEF00, 0x1EF00)    # Proprietary A (61184) and A2 (126720)
