/**
 * can_id.h — Decompose a 29-bit J1939 arbitration ID.
 *
 * Port of preprocess/frames/can_id_decompose.py.
 */
#ifndef CAN_ID_H
#define CAN_ID_H

#include <stdint.h>

/** Fields extracted from one 29-bit J1939 CAN ID. */
typedef struct {
    uint8_t  priority;       /**< 3-bit arbitration priority (0 = highest). */
    uint32_t pgn;            /**< Parameter Group Number. */
    uint8_t  source_address; /**< ECU that sent the frame. */
} CanId;

/**
 * Decompose a raw 29-bit J1939 arbitration ID.
 *
 * The high three bits (30-31 and any capture-format flags) are masked off
 * before decoding, matching the Python implementation.
 *
 * @param arb_id  Raw arbitration ID from the CAN peripheral.
 * @return        Populated CanId struct.
 */
CanId can_id_decompose(uint32_t arb_id);

#endif /* CAN_ID_H */
