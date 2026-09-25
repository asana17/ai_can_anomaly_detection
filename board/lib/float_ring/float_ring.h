#ifndef BOARD_FLOAT_RING_H
#define BOARD_FLOAT_RING_H

#include <stdbool.h>
#include <stdint.h>

/* A ring of floats over an array the caller owns, the oldest written over first. */
typedef struct {
	float *values;  /* the caller's array */
	uint32_t size;  /* its length */
	uint32_t start; /* where the oldest value is */
	uint32_t count; /* values held, at most size */
} FloatRing;

/**
 * @brief Set the ring over an array, empty.
 *
 * @param[out] ring The ring.
 * @param[in] values The array the values are kept in.
 * @param[in] size Its length. At least 1.
 */
static inline void float_ring_init(FloatRing *ring, float values[], uint32_t size)
{
	ring->values = values;
	ring->size = size;
	ring->start = 0u;
	ring->count = 0u;
}

/**
 * @brief Forget every value.
 *
 * @param[in,out] ring The ring.
 */
static inline void float_ring_clear(FloatRing *ring)
{
	ring->start = 0u;
	ring->count = 0u;
}

/**
 * @brief Give where in the array a value lies, counted from the oldest.
 *
 * @param[in] ring The ring.
 * @param[in] i 0 for the oldest.
 * @return The index in the caller's array.
 */
static inline uint32_t float_ring_index(const FloatRing *ring, uint32_t i)
{
	return (ring->start + i) % ring->size;
}

/**
 * @brief Keep a value, over the oldest when the ring is full.
 *
 * @param[in,out] ring The ring.
 * @param[in] value The value.
 */
static inline void float_ring_put(FloatRing *ring, float value)
{
	ring->values[float_ring_index(ring, ring->count)] = value;
	if(ring->count < ring->size) {
		ring->count++;
	} else {
		ring->start = float_ring_index(ring, 1u);
	}
}

/**
 * @brief Tell whether the ring holds size values.
 *
 * @param[in] ring The ring.
 * @retval true It is full.
 * @retval false It holds fewer.
 */
static inline bool float_ring_full(const FloatRing *ring)
{
	return ring->count == ring->size;
}

/**
 * @brief Give a value held, counted from the oldest.
 *
 * @param[in] ring The ring.
 * @param[in] i 0 for the oldest.
 * @return The value.
 * @pre @p i is less than the values held.
 */
static inline float float_ring_get(const FloatRing *ring, uint32_t i)
{
	return ring->values[float_ring_index(ring, i)];
}

#endif
