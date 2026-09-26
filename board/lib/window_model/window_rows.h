#ifndef BOARD_WINDOW_ROWS_H
#define BOARD_WINDOW_ROWS_H

#include <stdbool.h>
#include <stdint.h>
#include "model.h"
#include "row_ring.h"
#include "window_model_config.h"

/* The last rows with no gap among them, and when they make a window. */
typedef struct {
	RowRing row_ring;       /* the rows and their flags */
	uint32_t last_position; /* the position of the last row */
} WindowRows;

/* Start empty. */
static inline void window_rows_clear(WindowRows *window_rows)
{
	row_ring_clear(&window_rows->row_ring);
}

/* The rows held, at most WINDOW_MODEL_ROWS. */
static inline uint32_t window_rows_count(const WindowRows *window_rows)
{
	return row_ring_count(&window_rows->row_ring);
}

/* Start the rows again when position does not follow the last row's. */
static inline void window_rows_restart_on_gap(WindowRows *window_rows, uint32_t position)
{
	if (window_rows_count(window_rows) > 0u
		&& position != window_rows->last_position + 1u) {
		window_rows_clear(window_rows);
	}
	window_rows->last_position = position;
}

/*
 * True for the WINDOW_MODEL_ROWS-th row after a gap, and for every WINDOW_MODEL_STRIDE-th
 * row after that. position + 1 is the row's number counted from the gap.
 */
static inline bool window_rows_is_on_stride(uint32_t position)
{
	/* keeps the unsigned subtraction below from wrapping */
	if (position + 1u < WINDOW_MODEL_ROWS) {
		return false;
	}
	return (position + 1u - WINDOW_MODEL_ROWS) % WINDOW_MODEL_STRIDE == 0u;
}

/*
 * Add the row, its flag and its position, how many rows came right before it with no
 * gap. True when the rows now hold a whole window and the windowed model should score it.
 */
static inline bool window_rows_push(WindowRows *window_rows,
				    const float physical[MODEL_SIGNALS], bool flag,
				    uint32_t position)
{
	window_rows_restart_on_gap(window_rows, position);
	row_ring_push(&window_rows->row_ring, physical, flag);
	return window_rows_count(window_rows) == WINDOW_MODEL_ROWS
		&& window_rows_is_on_stride(position);
}

#endif
