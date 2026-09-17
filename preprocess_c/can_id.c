/**
 * can_id.c — Decompose a 29-bit J1939 arbitration ID.
 *
 * Port of preprocess/frames/can_id_decompose.py.
 *
 * J1939 bit layout (bit 0 = LSB of the 29-bit field):
 *
 *   bits 28..26  Priority (3 bits)
 *   bit  25      EDP — always 0 for standard J1939, ignored here
 *   bit  24      DP  — data page, selects the PGN number range
 *   bits 23..16  PF  — PDU Format
 *   bits 15..8   PS  — PDU Specific
 *   bits  7..0   SA  — Source Address
 *
 * PGN assembly:
 *   PF < 240  (PDU1): PS is a destination address → pgn = (DP<<16)|(PF<<8)
 *   PF >= 240 (PDU2): PS is part of the PGN      → pgn = (DP<<16)|(PF<<8)|PS
 */
#include "can_id.h"

#define EXTENDED_ID_MASK  0x1FFFFFFFu  /* keep only the 29 ID bits */
#define PDU1_FORMAT_LIMIT 240u         /* PF < 240 → PDU1 (peer-to-peer) */

CanId can_id_decompose(uint32_t arb_id)
{
    uint32_t id = arb_id & EXTENDED_ID_MASK;

    uint8_t  sa  = (uint8_t)( id        & 0xFFu);
    uint8_t  ps  = (uint8_t)((id >>  8) & 0xFFu);
    uint8_t  pf  = (uint8_t)((id >> 16) & 0xFFu);
    uint8_t  dp  = (uint8_t)((id >> 24) & 0x01u);
    uint8_t  pri = (uint8_t)((id >> 26) & 0x07u);

    uint32_t pgn = (pf < PDU1_FORMAT_LIMIT)
                   ? ((uint32_t)dp << 16) | ((uint32_t)pf << 8)
                   : ((uint32_t)dp << 16) | ((uint32_t)pf << 8) | ps;

    CanId result;
    result.priority       = pri;
    result.pgn            = pgn;
    result.source_address = sa;
    return result;
}
