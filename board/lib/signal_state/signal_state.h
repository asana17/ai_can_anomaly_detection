#ifndef BOARD_SIGNAL_STATE_H
#define BOARD_SIGNAL_STATE_H

#include <math.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "spn_decode.h"
#include "spn_spec.h"

#define SIGNAL_STATE_PAYLOAD 8 /* bytes of a classic CAN payload */
/* a slot per SPN_SPEC entry, of which the ones a PGN repeats stay unused */
#define SIGNAL_STATE_SLOTS SPN_SPEC_SIGNALS

typedef struct {
	uint8_t data[SIGNAL_STATE_PAYLOAD];
	uint8_t size;
	bool arrived;
} SignalStateSlot;

typedef struct {
	SignalStateSlot slots[SIGNAL_STATE_SLOTS];
} SignalState;

/**
 * @brief Find the slot of a PGN, the first SPN_SPEC entry that carries it.
 *
 * Every signal of one PGN lands on that PGN's first entry, so a frame is copied once.
 *
 * @param[in] pgn The PGN.
 * @return The slot's index, or SIGNAL_STATE_SLOTS for a PGN SPN_SPEC does not decode.
 */
static inline size_t signal_state_slot(uint32_t pgn)
{
	size_t i;

	for(i = 0; i < SPN_SPEC_SIGNALS; i++) {
		if(SPN_SPEC[i].pgn == pgn) {
			return i;
		}
	}
	return SIGNAL_STATE_SLOTS;
}

/**
 * @brief Empty every slot, as when no frame has arrived yet.
 *
 * @param[out] state The state.
 */
static inline void signal_state_clear(SignalState *state)
{
	memset(state, 0, sizeof(*state));
}

/**
 * @brief Keep a payload as the latest of its PGN.
 *
 * The C port of SignalState.update in preprocess/features/signal_state.py.
 *
 * @param[in,out] state The state.
 * @param[in] pgn The frame's PGN. One SPN_SPEC does not decode is ignored.
 * @param[in] data The payload.
 * @param[in] size Bytes in @p data, of which the first SIGNAL_STATE_PAYLOAD are kept.
 */
static inline void signal_state_update(SignalState *state, uint32_t pgn, const uint8_t data[],
				       size_t size)
{
	size_t slot = signal_state_slot(pgn);

	if(slot == SIGNAL_STATE_SLOTS) {
		return;
	}
	if(size > SIGNAL_STATE_PAYLOAD) {
		size = SIGNAL_STATE_PAYLOAD;
	}
	memcpy(state->slots[slot].data, data, size);
	state->slots[slot].size = (uint8_t)size;
	state->slots[slot].arrived = true;
}

/**
 * @brief Decode every signal from its PGN's latest payload.
 *
 * The C port of SignalState.row in preprocess/features/signal_state.py.
 *
 * @param[in] state The state.
 * @param[out] row The physical values in the order of SIGNALS. A value J1939 reserves,
 *                 or one whose PGN has no slot or has not arrived, is NaN.
 * @pre @p row has room for SPN_SPEC_SIGNALS elements.
 */
static inline void signal_state_row(const SignalState *state, float row[])
{
	size_t i;

	for(i = 0; i < SPN_SPEC_SIGNALS; i++) {
		size_t at = signal_state_slot(SPN_SPEC[i].pgn);

		if(at == SIGNAL_STATE_SLOTS || !state->slots[at].arrived
		   || !spn_decode(state->slots[at].data, state->slots[at].size,
				  &SPN_SPEC[i].field, &row[i])) {
			row[i] = NAN;
		}
	}
}

/**
 * @brief Check whether every PGN of SPN_SPEC has arrived at least once.
 *
 * The C port of SignalState.ready in preprocess/features/signal_state.py.
 *
 * @param[in] state The state.
 * @retval true Every PGN's slot holds a payload.
 * @retval false A PGN has not arrived.
 */
static inline bool signal_state_ready(const SignalState *state)
{
	size_t i;

	for(i = 0; i < SPN_SPEC_SIGNALS; i++) {
		if(!state->slots[signal_state_slot(SPN_SPEC[i].pgn)].arrived) {
			return false;
		}
	}
	return true;
}

#endif
