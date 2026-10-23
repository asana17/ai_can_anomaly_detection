#ifndef BOARD_RECENT_ROWS_H
#define BOARD_RECENT_ROWS_H

#include <stdint.h>
#include <string.h>
#include "signals.h"

/*
 * The most rows before the row judged that a rule reads,
 * REPEATED_SIGNAL_LAG + REPEATED_SIGNAL_ROWS - 1.
 */
#define RECENT_ROWS_ROWS 19u

/* A ring of the last RECENT_ROWS_ROWS rows, for the rules that read earlier rows. */
typedef struct {
	float rows[RECENT_ROWS_ROWS][SIGNAL_COUNT];
	uint32_t start; /* the slot of the oldest row */
	uint32_t count; /* rows held, from start on, wrapping at RECENT_ROWS_ROWS */
} RecentRows;

/**
 * @brief Empty the ring.
 *
 * @param[out] recent The ring.
 */
static inline void recent_rows_clear(RecentRows *recent)
{
	recent->start = 0u;
	recent->count = 0u;
}

/**
 * @brief Give the slot of the row at index, counted from the oldest.
 *
 * @param[in] recent The ring.
 * @param[in] index 0 for the oldest, the one at start.
 * @return The slot.
 */
static inline uint32_t recent_rows_index(const RecentRows *recent, uint32_t index)
{
	return (recent->start + index) % RECENT_ROWS_ROWS;
}

/**
 * @brief Add a row, over the oldest when the ring is full.
 *
 * @param[in,out] recent The ring.
 * @param[in] row Physical values in the order of SIGNALS.
 */
static inline void recent_rows_push(RecentRows *recent, const float row[])
{
	memcpy(recent->rows[recent_rows_index(recent, recent->count)], row,
	       sizeof(recent->rows[0]));
	if (recent->count < RECENT_ROWS_ROWS) {
		recent->count = recent->count + 1u;
	} else {
		recent->start = (recent->start + 1u) % RECENT_ROWS_ROWS;
	}
}

/**
 * @brief Give the number of rows held.
 *
 * @param[in] recent The ring.
 * @return The rows held, at most RECENT_ROWS_ROWS.
 */
static inline uint32_t recent_rows_count(const RecentRows *recent)
{
	return recent->count;
}

/**
 * @brief Give the row at index, counted from the oldest.
 *
 * @param[in] recent The ring.
 * @param[in] index 0 for the oldest, below recent_rows_count().
 * @return The row's SIGNAL_COUNT values.
 */
static inline const float *recent_rows_row(const RecentRows *recent, uint32_t index)
{
	return recent->rows[recent_rows_index(recent, index)];
}

#endif
