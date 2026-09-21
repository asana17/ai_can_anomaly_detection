#ifndef BOARD_CAN_ID_H
#define BOARD_CAN_ID_H

#include <stdint.h>

#define CAN_ID_EXTENDED_MASK 0x1FFFFFFFu
#define CAN_ID_PDU1_FORMAT_LIMIT 240u /* PF < 240 is PDU1 (destination-specific), else PDU2 */

typedef struct {
	uint8_t priority;
	uint32_t pgn;
	uint8_t source_address;
} CanId;

/**
 * @brief Decompose a 29-bit J1939 arbitration ID into priority, PGN and source address.
 *
 * The C port of preprocess/frames/can_id_decompose.py.
 *
 * @param[in] arb_id The arbitration ID. Bits above 29 are ignored.
 * @return The priority, PGN and source address encoded in @p arb_id.
 */
static inline CanId can_id_decompose(uint32_t arb_id)
{
	uint32_t ident = arb_id & CAN_ID_EXTENDED_MASK;
	uint32_t pdu_specific = (ident >> 8) & 0xFFu;
	uint32_t pdu_format = (ident >> 16) & 0xFFu;
	uint32_t data_page = (ident >> 24) & 0x1u;
	CanId out;

	out.priority = (uint8_t)((ident >> 26) & 0x7u);
	out.source_address = (uint8_t)(ident & 0xFFu);
	out.pgn = (data_page << 16) | (pdu_format << 8);
	if(pdu_format >= CAN_ID_PDU1_FORMAT_LIMIT) {
		/* PDU2: PDU Specific is part of the PGN. In PDU1 it is a destination address. */
		out.pgn |= pdu_specific;
	}
	return out;
}

#endif
