#ifndef BOARD_ROW_RING_H
#define BOARD_ROW_RING_H

#include <stdbool.h>
#include <stdint.h>
#include "model.h"
#include "window_model_config.h"

#define ROW_RING_ROWS WINDOW_MODEL_ROWS

/* One row in a RowRing, with what the windowed model needs about it. */
typedef struct {
	uint32_t no; /* the row's number, counting ticks */
	float physical[SIGNAL_COUNT];
	bool flag; /* a rule or the instant model flagged the row */
	uint32_t row_count_since_gap; /* this row's place since the last gap, from 0 */
} RowRingEntry;

/* A ring of the last ROW_RING_ROWS rows. */
typedef struct {
	RowRingEntry entries[ROW_RING_ROWS];
	uint32_t start; /* the slot of the oldest row */
	uint32_t count; /* rows held, from start on, wrapping at ROW_RING_ROWS */
} RowRing;

/**
 * @brief Empty the ring.
 *
 * @param[out] ring The ring.
 */
static inline void row_ring_clear(RowRing *ring)
{
	ring->start = 0u;
	ring->count = 0u;
}

/**
 * @brief Give the slot of the row at index, counted from the oldest.
 *
 * @param[in] ring The ring.
 * @param[in] index 0 for the oldest, the one at start.
 * @return The slot.
 */
static inline uint32_t row_ring_index(const RowRing *ring, uint32_t index)
{
	return (ring->start + index) % ROW_RING_ROWS;
}

/**
 * @brief Add a row, over the oldest when the ring is full.
 *
 * @param[in,out] ring The ring.
 * @param[in] entry The row.
 */
static inline void row_ring_push(RowRing *ring, const RowRingEntry *entry)
{
	ring->entries[row_ring_index(ring, ring->count)] = *entry;
	if (ring->count < ROW_RING_ROWS) {
		ring->count = ring->count + 1u;
	} else {
		ring->start = (ring->start + 1u) % ROW_RING_ROWS;
	}
}

/**
 * @brief Give the number of rows held.
 *
 * @param[in] ring The ring.
 * @return The rows held, at most ROW_RING_ROWS.
 */
static inline uint32_t row_ring_count(const RowRing *ring)
{
	return ring->count;
}

/**
 * @brief Give the row at index, counted from the oldest.
 *
 * @param[in] ring The ring.
 * @param[in] index 0 for the oldest, below row_ring_count().
 * @return The row.
 */
static inline const RowRingEntry *row_ring_entry(const RowRing *ring, uint32_t index)
{
	return &ring->entries[row_ring_index(ring, index)];
}

#endif
