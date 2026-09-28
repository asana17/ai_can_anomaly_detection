#ifndef BOARD_FRAME_RING_H
#define BOARD_FRAME_RING_H

#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define FRAME_RING_FRAMES 4096u /* 64 KB, a power of two so the position wraps cleanly */
#define FRAME_RING_DATA_BYTES 8u
/* the longest time since the frame before that the 3 bytes hold, in us */
#define FRAME_RING_DELTA_MAX 0xFFFFFFu

/*
 * A received frame in one Flash write of 16 bytes. The time since the frame before sits
 * in the low 3 bytes of delta_and_size and the size in the top byte.
 */
typedef struct {
	uint32_t delta_and_size; /* us since the frame before, then the size */
	uint32_t arb_id;         /* the 29-bit arbitration ID */
	uint8_t data[FRAME_RING_DATA_BYTES]; /* the payload, 0 past size */
} FrameRingEntry;

/*
 * A ring of the last FRAME_RING_FRAMES frames. One writer, the CAN receive interrupt or
 * the replay, pushes. The place to write is one volatile word, so a reader reads it once
 * without stopping interrupts, and a place it keeps names the same frame until
 * overwritten.
 */
typedef struct {
	FrameRingEntry entries[FRAME_RING_FRAMES];
	volatile uint32_t position; /* the place of the next frame, only ever growing */
	uint32_t last_time;         /* the last frame's time, in the writer's clock */
	uint32_t time_units_per_us; /* the writer's clock units in 1 us */
} FrameRing;

/**
 * @brief Empty the ring.
 *
 * @param[out] ring The ring.
 * @param[in] time_units_per_us The writer's clock units in 1 us.
 */
static inline void frame_ring_clear(FrameRing *ring, uint32_t time_units_per_us)
{
	ring->position = 0u;
	ring->last_time = 0u;
	ring->time_units_per_us = time_units_per_us;
}

/**
 * @brief Give the slot of the frame at a place.
 *
 * @param[in] position The place, as position was when the frame was pushed.
 * @return The slot.
 */
static inline uint32_t frame_ring_index(uint32_t position)
{
	return position % FRAME_RING_FRAMES;
}

/**
 * @brief Add a frame, over the oldest when the ring is full.
 *
 * The first frame's time since the frame before is from time 0 of the writer's clock.
 * A time longer than FRAME_RING_DELTA_MAX is kept as FRAME_RING_DELTA_MAX.
 *
 * @param[in,out] ring The ring.
 * @param[in] arb_id The 29-bit arbitration ID.
 * @param[in] data The payload.
 * @param[in] size Bytes in @p data, up to FRAME_RING_DATA_BYTES.
 * @param[in] time The frame's receive time, in the writer's clock.
 */
static inline void frame_ring_push(FrameRing *ring, uint32_t arb_id, const uint8_t data[],
	size_t size, uint32_t time)
{
	FrameRingEntry *entry = &ring->entries[frame_ring_index(ring->position)];
	uint32_t delta = (time - ring->last_time) / ring->time_units_per_us;

	if (delta > FRAME_RING_DELTA_MAX) {
		delta = FRAME_RING_DELTA_MAX;
	}
	entry->delta_and_size = delta | ((uint32_t)size << 24);
	entry->arb_id = arb_id;
	memset(entry->data, 0, FRAME_RING_DATA_BYTES);
	memcpy(entry->data, data, size);
	ring->last_time = time;
	ring->position = ring->position + 1u;
}

/**
 * @brief Give the frame at a place.
 *
 * @param[in] ring The ring.
 * @param[in] position The place, within FRAME_RING_FRAMES before position.
 * @return The frame.
 */
static inline const FrameRingEntry *frame_ring_entry(const FrameRing *ring,
	uint32_t position)
{
	return &ring->entries[frame_ring_index(position)];
}

#endif
