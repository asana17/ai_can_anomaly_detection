#ifndef BOARD_ROW_RING_H
#define BOARD_ROW_RING_H

#include <stdbool.h>
#include <stdint.h>
#include "model.h"
#include "window_model_config.h"

#define ROW_RING_ROWS WINDOW_MODEL_ROWS

/* A ring of the last ROW_RING_ROWS rows and their flags. */
typedef struct {
	float physical[ROW_RING_ROWS][MODEL_SIGNALS];
	uint8_t flags[ROW_RING_ROWS];
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
 * @brief Give the slot of the i-th oldest row.
 *
 * @param[in] ring The ring.
 * @param[in] i 0 for the oldest, the one at start.
 * @return The slot.
 */
static inline uint32_t row_ring_index(const RowRing *ring, uint32_t i)
{
	return (ring->start + i) % ROW_RING_ROWS;
}

/**
 * @brief Add a row and its flag, over the oldest when the ring is full.
 *
 * @param[in,out] ring The ring.
 * @param[in] physical The row.
 * @param[in] flag Its flag.
 */
static inline void row_ring_push(RowRing *ring, const float physical[MODEL_SIGNALS],
				 bool flag)
{
	uint32_t at = row_ring_index(ring, ring->count);
	uint32_t i;

	for(i = 0u; i < MODEL_SIGNALS; i++) {
		ring->physical[at][i] = physical[i];
	}
	ring->flags[at] = flag;
	if(ring->count < ROW_RING_ROWS) {
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
 * @brief Give the i-th oldest row.
 *
 * @param[in] ring The ring.
 * @param[in] i 0 for the oldest, below row_ring_count().
 * @return The row's MODEL_SIGNALS values.
 */
static inline const float *row_ring_physical(const RowRing *ring, uint32_t i)
{
	return ring->physical[row_ring_index(ring, i)];
}

/**
 * @brief Give the flag of the i-th oldest row.
 *
 * @param[in] ring The ring.
 * @param[in] i 0 for the oldest, below row_ring_count().
 * @return The row's flag.
 */
static inline bool row_ring_flag(const RowRing *ring, uint32_t i)
{
	return ring->flags[row_ring_index(ring, i)];
}

#endif
