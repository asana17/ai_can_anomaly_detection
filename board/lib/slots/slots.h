#ifndef BOARD_SLOTS_H
#define BOARD_SLOTS_H

#include <stddef.h>
#include <stdint.h>

#include "can_id.h"
#include "signal_state.h"

typedef struct {
	SignalState state; /* the latest payload of each PGN */
	uint32_t frames; /* frames stored, so a reader can tell the bus has gone quiet */
	uint32_t time; /* receive time of the latest frame, in the driver's clock */
} Slots;

/**
 * @brief Keep a received frame as the latest of its PGN.
 *
 * What the CAN receive interrupt calls for each frame, and all it needs to call. It does
 * what `resample` in preprocess/features/grid_sample.py does with a frame, decomposing
 * its ID and updating the state. A frame whose PGN the state does not decode still
 * counts in @c frames, since the PC measures a gap on the whole bus.
 *
 * @param[in,out] slots The slots.
 * @param[in] arb_id The 29-bit arbitration ID.
 * @param[in] data The payload.
 * @param[in] size Bytes in @p data.
 * @param[in] time The frame's receive time, in the driver's clock.
 */
static inline void slots_store(Slots *slots, uint32_t arb_id, const uint8_t data[],
	size_t size, uint32_t time)
{
	signal_state_update(&slots->state, can_id_decompose(arb_id).pgn, data, size);
	slots->frames = slots->frames + 1u;
	slots->time = time;
}

#endif
