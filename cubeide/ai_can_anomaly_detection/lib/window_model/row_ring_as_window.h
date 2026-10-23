#ifndef BOARD_ROW_RING_AS_WINDOW_H
#define BOARD_ROW_RING_AS_WINDOW_H

#include <stdbool.h>
#include <stdint.h>
#include "model.h"
#include "row_ring.h"
#include "window_model_config.h"
#include "window_model_stride.h"

/*
 * The rows window scoring and detect keeps for the windowed model. It takes every row
 * from the shared ring and keeps the last ones itself, so after running late it can still
 * build a window whose last row it missed.
 */
typedef struct {
	RowRing row_ring;
} RowRingAsWindow;

/**
 * @brief Empty the window.
 *
 * @param[out] window The window.
 */
static inline void row_ring_as_window_clear(RowRingAsWindow *window)
{
	row_ring_clear(&window->row_ring);
}

/**
 * @brief Give the number of rows held.
 *
 * @param[in] window The window.
 * @return The rows held, at most WINDOW_MODEL_ROWS.
 */
static inline uint32_t row_ring_as_window_count(const RowRingAsWindow *window)
{
	return row_ring_count(&window->row_ring);
}

/**
 * @brief Give the row at index, counted from the oldest.
 *
 * @param[in] window The window.
 * @param[in] index 0 for the oldest, below row_ring_as_window_count().
 * @return The row.
 */
static inline const RowRingEntry *row_ring_as_window_entry(const RowRingAsWindow *window,
							   uint32_t index)
{
	return row_ring_entry(&window->row_ring, index);
}

/* Empty the window when row_count_since_gap does not follow the newest row's. */
static inline void row_ring_as_window_restart_on_gap(RowRingAsWindow *window,
						     uint32_t row_count_since_gap)
{
	uint32_t held = row_ring_as_window_count(window);
	const RowRingEntry *newest;

	if (held == 0u) {
		return;
	}
	newest = row_ring_as_window_entry(window, held - 1u);
	if (row_count_since_gap != newest->row_count_since_gap + 1u) {
		row_ring_as_window_clear(window);
	}
}

/*
 * True for the WINDOW_MODEL_ROWS-th row after a gap, and for every WINDOW_MODEL_STRIDE-th
 * row after that. row_count_since_gap + 1 is the row's number counted from the gap.
 */
static inline bool row_ring_as_window_is_on_stride(uint32_t row_count_since_gap)
{
	/* keeps the unsigned subtraction below from wrapping */
	if (row_count_since_gap + 1u < WINDOW_MODEL_ROWS) {
		return false;
	}
	return (row_count_since_gap + 1u - WINDOW_MODEL_ROWS) % WINDOW_MODEL_STRIDE == 0u;
}

/**
 * @brief Add the row.
 *
 * @param[in,out] window The window.
 * @param[in] entry The row.
 */
static inline void row_ring_as_window_push(RowRingAsWindow *window, const RowRingEntry *entry)
{
	row_ring_as_window_restart_on_gap(window, entry->row_count_since_gap);
	row_ring_push(&window->row_ring, entry);
}

/**
 * @brief Check whether the window is complete.
 *
 * @param[in] window The window.
 * @retval true It holds WINDOW_MODEL_ROWS rows, and a window ends at the newest.
 * @retval false It does not.
 */
static inline bool row_ring_as_window_is_complete(const RowRingAsWindow *window)
{
	uint32_t held = row_ring_as_window_count(window);

	if (held != WINDOW_MODEL_ROWS) {
		return false;
	}
	return row_ring_as_window_is_on_stride(
		row_ring_as_window_entry(window, held - 1u)->row_count_since_gap);
}

#endif
