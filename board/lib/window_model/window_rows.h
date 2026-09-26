#ifndef BOARD_WINDOW_ROWS_H
#define BOARD_WINDOW_ROWS_H

#include <stdbool.h>
#include <stdint.h>
#include "model.h"
#include "row_ring.h"
#include "window_model_config.h"

/* The last rows of an unbroken stretch of row numbers, and when they make a window. */
typedef struct {
	RowRing ring;     /* the rows and their flags */
	uint32_t last_no; /* number of the last row */
	uint32_t count;   /* rows since the numbers last broke */
} WindowRows;

/* Start empty. */
static inline void window_rows_clear(WindowRows *rows)
{
	row_ring_clear(&rows->ring);
	rows->count = 0u;
}

/* Take the next row number. Empty the rows when it does not follow the last. */
static inline void window_rows_restart_on_gap(WindowRows *rows, uint32_t no)
{
	if(rows->count > 0u && no != rows->last_no + 1u) {
		window_rows_clear(rows);
	}
	rows->last_no = no;
}

/* Add the row and its flag. True when a new window is ready. */
static inline bool window_rows_push(WindowRows *rows, const float physical[MODEL_SIGNALS],
				    bool flag)
{
	row_ring_push(&rows->ring, physical, flag);
	rows->count = rows->count + 1u;
	/* first window at WINDOW_MODEL_ROWS rows, then every WINDOW_MODEL_STRIDE rows */
	return rows->count >= WINDOW_MODEL_ROWS
		&& (rows->count - WINDOW_MODEL_ROWS) % WINDOW_MODEL_STRIDE == 0u;
}

#endif
