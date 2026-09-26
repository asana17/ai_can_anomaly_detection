#ifndef BOARD_WINDOW_ROWS_H
#define BOARD_WINDOW_ROWS_H

#include <stdbool.h>
#include <stdint.h>
#include "model.h"
#include "row_ring.h"
#include "window_model_config.h"

/*
 * The rows window scoring and detect keeps for the windowed model, in a RowRing. It takes
 * every row from the shared ring and keeps the last ones itself, so after running late it
 * can still build a window whose last row it missed.
 */

/* Empty the ring when row_count_since_gap does not follow the newest row's. */
static inline void window_rows_restart_on_gap(RowRing *row_ring,
					      uint32_t row_count_since_gap)
{
	uint32_t held = row_ring_count(row_ring);
	const RowRingEntry *newest;

	if (held == 0u) {
		return;
	}
	newest = row_ring_entry(row_ring, held - 1u);
	if (row_count_since_gap != newest->row_count_since_gap + 1u) {
		row_ring_clear(row_ring);
	}
}

/*
 * True for the WINDOW_MODEL_ROWS-th row after a gap, and for every WINDOW_MODEL_STRIDE-th
 * row after that. row_count_since_gap + 1 is the row's number counted from the gap.
 */
static inline bool window_rows_is_on_stride(uint32_t row_count_since_gap)
{
	/* keeps the unsigned subtraction below from wrapping */
	if (row_count_since_gap + 1u < WINDOW_MODEL_ROWS) {
		return false;
	}
	return (row_count_since_gap + 1u - WINDOW_MODEL_ROWS) % WINDOW_MODEL_STRIDE == 0u;
}

/* Add the row. True when the ring holds a whole window and the model should score it. */
static inline bool window_rows_push(RowRing *row_ring, const RowRingEntry *entry)
{
	window_rows_restart_on_gap(row_ring, entry->row_count_since_gap);
	row_ring_push(row_ring, entry);
	return row_ring_count(row_ring) == WINDOW_MODEL_ROWS
		&& window_rows_is_on_stride(entry->row_count_since_gap);
}

#endif
