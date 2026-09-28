#ifndef BOARD_REPEATED_SIGNAL_H
#define BOARD_REPEATED_SIGNAL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "recent_rows.h"
#include "signals.h"

/* LAG and ROWS in rules/sequence/repeated_signal.py */
#define REPEATED_SIGNAL_LAG 10u
#define REPEATED_SIGNAL_ROWS 10u

#if RECENT_ROWS_ROWS < REPEATED_SIGNAL_LAG + REPEATED_SIGNAL_ROWS - 1u
#error "RecentRows holds fewer rows than repeated_signal reads"
#endif

/* WATCHED in rules/sequence/repeated_signal.py */
static const size_t REPEATED_SIGNAL_WATCHED[] = {
	SIGNAL_ENGINE_SPEED, SIGNAL_INPUT_SHAFT_SPEED, SIGNAL_YAW_RATE, SIGNAL_LATERAL_ACCEL,
};
#define REPEATED_SIGNAL_SIGNALS \
	(sizeof(REPEATED_SIGNAL_WATCHED) / sizeof(REPEATED_SIGNAL_WATCHED[0]))

/**
 * @brief Give the row @p back rows before @p row, @p row itself at 0.
 *
 * @param[in] recent The rows before @p row since a gap.
 * @param[in] row Physical values in the order of SIGNALS.
 * @param[in] back Rows back, at most recent_rows_count().
 * @return The row's SIGNAL_COUNT values.
 */
static inline const float *repeated_signal_row_back(const RecentRows *recent,
	const float row[], uint32_t back)
{
	if (back == 0u) {
		return row;
	}
	return recent_rows_row(recent, recent_rows_count(recent) - back);
}

/**
 * @brief Check whether a watched signal read what it read LAG rows before, on each of
 *        the row and the ROWS - 1 rows before it.
 *
 * The C port of rules/sequence/repeated_signal.py.
 *
 * @param[in] recent The rows before @p row since a gap.
 * @param[in] row Physical values in the order of SIGNALS.
 * @retval true A watched signal repeated over ROWS rows.
 * @retval false None did, a NaN broke the repeat, or @p recent holds fewer than
 *               LAG + ROWS - 1 rows.
 */
static inline bool repeated_signal_hits(const RecentRows *recent, const float row[])
{
	size_t i;
	size_t signal;
	uint32_t back;
	bool repeated;

	if (recent_rows_count(recent) < REPEATED_SIGNAL_LAG + REPEATED_SIGNAL_ROWS - 1u) {
		return false;
	}
	for (i = 0; i < REPEATED_SIGNAL_SIGNALS; i++) {
		signal = REPEATED_SIGNAL_WATCHED[i];
		repeated = true;
		for (back = 0u; back < REPEATED_SIGNAL_ROWS && repeated; back++) {
			/* A NaN compares false, as in the Python rule. */
			repeated = repeated_signal_row_back(recent, row, back)[signal]
				== repeated_signal_row_back(recent, row,
					back + REPEATED_SIGNAL_LAG)[signal];
		}
		if (repeated) {
			return true;
		}
	}
	return false;
}

#endif
