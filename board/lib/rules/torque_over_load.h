#ifndef BOARD_TORQUE_OVER_LOAD_H
#define BOARD_TORQUE_OVER_LOAD_H

#include <stdbool.h>
#include <stdint.h>
#include "float_ring.h"

/* ROWS and LIMIT in rules/sequence/torque_over_load.py */
#define TORQUE_OVER_LOAD_ROWS 10u
#define TORQUE_OVER_LOAD_LIMIT 3.5f /* % */

/* Torque minus load of the last rows of the run. */
typedef struct {
	float steps[TORQUE_OVER_LOAD_ROWS];
	FloatRing ring; /* points into steps, so a copy of the struct breaks it */
	uint32_t no; /* the number of the last row given */
} TorqueOverLoad;

/**
 * @brief Forget every row, as before the first.
 *
 * @param[out] state The rows kept.
 */
static inline void torque_over_load_clear(TorqueOverLoad *state)
{
	float_ring_init(&state->ring, state->steps, TORQUE_OVER_LOAD_ROWS);
	state->no = 0u;
}

/**
 * @brief Keep a row's torque minus load.
 *
 * @param[in,out] state The rows kept.
 * @param[in] actual_engine_torque The row's actual engine torque in %.
 * @param[in] engine_load The row's engine load in %.
 * @param[in] no The row's number, the tick it was built on.
 * @param[in] position The rows before the row in its run.
 */
static inline void torque_over_load_put(TorqueOverLoad *state,
					float actual_engine_torque, float engine_load,
					uint32_t no, uint32_t position)
{
	/* A new run, or a row after a missed one, starts over. A window never spans either. */
	if(position == 0u || no != state->no + 1u) {
		float_ring_clear(&state->ring);
	}
	state->no = no;
	float_ring_put(&state->ring, actual_engine_torque - engine_load);
}

/**
 * @brief Check whether torque sits above load over the last ROWS rows kept.
 *
 * The C port of rules/sequence/torque_over_load.py.
 *
 * @param[in] state The rows kept.
 * @retval true The mean of torque minus load is above the limit.
 * @retval false It is not, a NaN is in the window, or fewer than ROWS rows of the run
 *               have been kept one number after another.
 */
static inline bool torque_over_load_hits(const TorqueOverLoad *state)
{
	uint32_t i;
	float total = 0.0f;

	if(!float_ring_full(&state->ring)) {
		return false;
	}
	/* Oldest first, the order the Python rule adds in. */
	for(i = 0u; i < TORQUE_OVER_LOAD_ROWS; i++) {
		total += float_ring_get(&state->ring, i);
	}
	return total / (float)TORQUE_OVER_LOAD_ROWS > TORQUE_OVER_LOAD_LIMIT;
}

#endif
