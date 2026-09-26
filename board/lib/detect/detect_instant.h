#ifndef BOARD_DETECT_INSTANT_H
#define BOARD_DETECT_INSTANT_H

#include <stdbool.h>
#include <stdint.h>

/* Rows an alarm looks back over, Settings.N on the PC. */
#define DETECT_INSTANT_ROWS 10u

typedef struct {
	float threshold;                      /* the score above which a row is flagged */
	uint32_t k;                           /* flagged rows in the ring an alarm needs */
	bool ring_flags[DETECT_INSTANT_ROWS]; /* a ring of the last rows' flags */
	uint32_t ring_start;                  /* the slot of the oldest flag */
	uint32_t ring_count;                  /* flags in the ring, from ring_start on */
	uint32_t flagged_count_in_ring;       /* true flags in the ring */
	uint32_t number;                      /* the number of the last row added */
} DetectInstant;

/**
 * @brief Empty the ring.
 *
 * @param[out] state The state.
 */
static inline void detect_instant_clear_ring(DetectInstant *state)
{
	state->ring_start = 0u;
	state->ring_count = 0u;
	state->flagged_count_in_ring = 0u;
}

/**
 * @brief Set the threshold and k, and empty the ring.
 *
 * @param[out] state The state.
 * @param[in] threshold The threshold calibrate took on the PC.
 * @param[in] k Flagged rows among the last DETECT_INSTANT_ROWS an alarm needs.
 */
static inline void detect_instant_init(DetectInstant *state, float threshold,
				       uint32_t k)
{
	state->threshold = threshold;
	state->k = k;
	state->number = 0u;
	detect_instant_clear_ring(state);
}

/**
 * @brief Drop the oldest flag from the ring.
 *
 * @param[in,out] state The state.
 */
static inline void detect_instant_drop_oldest_flag(DetectInstant *state)
{
	if(state->ring_flags[state->ring_start]) {
		state->flagged_count_in_ring--;
	}
	state->ring_start = (state->ring_start + 1u) % DETECT_INSTANT_ROWS;
	state->ring_count--;
}

/**
 * @brief Put a flag after the newest one in the ring. The ring must not be full.
 *
 * @param[in,out] state The state.
 * @param[in] flag The flag.
 */
static inline void detect_instant_append_flag(DetectInstant *state, bool flag)
{
	uint32_t end = (state->ring_start + state->ring_count) % DETECT_INSTANT_ROWS;

	state->ring_flags[end] = flag;
	state->ring_count++;
	if(flag) {
		state->flagged_count_in_ring++;
	}
}

/**
 * @brief Flag a row and add its flag to the ring, over the oldest when it is full.
 *
 * A row is flagged when a rule hit it or its score is above the threshold. A NaN score
 * is never above it. A gap in the row numbers empties the ring first, as a new segment
 * does on the PC.
 *
 * @param[in,out] state The state.
 * @param[in] number The row's number.
 * @param[in] score The model's score for the row, NaN where it did not score it.
 * @param[in] rule_hit Whether a rule hit the row.
 */
static inline void detect_instant_add_row(DetectInstant *state, uint32_t number,
					  float score, bool rule_hit)
{
	bool flag = score > state->threshold || rule_hit;

	if(number != state->number + 1u) {
		detect_instant_clear_ring(state);
	}
	if(state->ring_count == DETECT_INSTANT_ROWS) {
		detect_instant_drop_oldest_flag(state);
	}
	detect_instant_append_flag(state, flag);
	state->number = number;
}

/**
 * @brief Check whether the row added last is flagged.
 *
 * @param[in] state The state.
 * @retval true It is flagged.
 * @retval false It is not, or no row has been added.
 */
static inline bool detect_instant_last_row_flagged(const DetectInstant *state)
{
	uint32_t last;

	if(state->ring_count == 0u) {
		return false;
	}
	last = (state->ring_start + state->ring_count - 1u) % DETECT_INSTANT_ROWS;
	return state->ring_flags[last];
}

/**
 * @brief Check whether the last rows raise an alarm.
 *
 * The C port of `alarmed_rows` in detect/alarm.py at n DETECT_INSTANT_ROWS.
 *
 * @param[in] state The state.
 * @retval true k of the last DETECT_INSTANT_ROWS rows are flagged.
 * @retval false They are not.
 */
static inline bool detect_instant_alarmed(const DetectInstant *state)
{
	return state->flagged_count_in_ring >= state->k;
}

#endif
