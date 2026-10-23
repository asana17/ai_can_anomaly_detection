#ifndef BOARD_TORQUE_OVER_LOAD_H
#define BOARD_TORQUE_OVER_LOAD_H

#include <stdbool.h>
#include <stdint.h>
#include "recent_rows.h"
#include "signals.h"

/* ROWS and LIMIT in rules/sequence/torque_over_load.py */
#define TORQUE_OVER_LOAD_ROWS 10u
#define TORQUE_OVER_LOAD_LIMIT 3.5f /* % */

#if RECENT_ROWS_ROWS < TORQUE_OVER_LOAD_ROWS - 1u
#error "RecentRows holds fewer rows than torque_over_load reads"
#endif

/**
 * @brief Check whether torque sits above load over the row and the rows before it.
 *
 * The C port of rules/sequence/torque_over_load.py.
 *
 * @param[in] recent The rows before @p row since a gap.
 * @param[in] row Physical values in the order of SIGNALS.
 * @retval true The mean of torque minus load over ROWS rows is above the limit.
 * @retval false It is not, a NaN is among the rows, or @p recent holds fewer than
 *               ROWS - 1 rows.
 */
static inline bool torque_over_load_hits(const RecentRows *recent, const float row[])
{
	uint32_t held = recent_rows_count(recent);
	uint32_t index;
	const float *before;
	float total = 0.0f;

	if (held < TORQUE_OVER_LOAD_ROWS - 1u) {
		return false;
	}
	/* Oldest first, the order the Python rule adds in. */
	for (index = held - (TORQUE_OVER_LOAD_ROWS - 1u); index < held; index++) {
		before = recent_rows_row(recent, index);
		total += before[SIGNAL_ACTUAL_ENGINE_TORQUE] - before[SIGNAL_ENGINE_LOAD];
	}
	total += row[SIGNAL_ACTUAL_ENGINE_TORQUE] - row[SIGNAL_ENGINE_LOAD];
	return total / (float)TORQUE_OVER_LOAD_ROWS > TORQUE_OVER_LOAD_LIMIT;
}

#endif
