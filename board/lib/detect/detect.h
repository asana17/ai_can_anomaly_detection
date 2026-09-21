#ifndef BOARD_DETECT_H
#define BOARD_DETECT_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
	uint32_t number; /* the number of the last row that went in */
	uint32_t run;    /* rows flagged in a row, ending at that row */
	bool seen;       /* a row has gone in */
} DetectState;

/**
 * @brief Forget the run, as before the first row.
 *
 * @param[out] state The state.
 */
static inline void detect_clear(DetectState *state)
{
	state->number = 0;
	state->run = 0;
	state->seen = false;
}

/**
 * @brief Check whether a rule hit a row or its score is above the threshold.
 *
 * The C port of the flag `alarmed_rows` raises in detect/alarm.py.
 *
 * @param[in] score The model's score for the row, NaN where it did not score it.
 * @param[in] threshold The threshold calibrate took on the PC.
 * @param[in] rule_hit Whether a rule hit the row.
 * @retval true The row is flagged. A NaN score is never above @p threshold.
 * @retval false It is not.
 */
static inline bool detect_flagged(float score, float threshold, bool rule_hit)
{
	return score > threshold || rule_hit;
}

/**
 * @brief Take a row and tell whether it raises an alarm.
 *
 * The C port of `alarmed_rows` in detect/alarm.py, a row at a time. A run of flagged
 * rows carries only from one row number to the next, so a gap restarts it as a new
 * segment does on the PC.
 *
 * @param[in,out] state The state.
 * @param[in] number The row's number.
 * @param[in] score The model's score for the row.
 * @param[in] threshold The threshold calibrate took on the PC.
 * @param[in] rule_hit Whether a rule hit the row.
 * @param[in] hold Flagged rows in a row an alarm needs. 0 counts as 1.
 * @retval true The row ends a run of @p hold flagged rows.
 * @retval false It does not.
 */
static inline bool detect_alarmed(DetectState *state, uint32_t number, float score,
				    float threshold, bool rule_hit, uint32_t hold)
{
	bool follows = state->seen && number == state->number + 1u;

	if(!detect_flagged(score, threshold, rule_hit)) {
		state->run = 0;
	} else if(follows) {
		state->run = state->run + 1u;
	} else {
		state->run = 1u;
	}
	state->number = number;
	state->seen = true;
	if(hold < 1u) {
		hold = 1u;
	}
	return state->run >= hold;
}

#endif
