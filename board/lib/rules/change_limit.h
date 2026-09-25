#ifndef BOARD_CHANGE_LIMIT_H
#define BOARD_CHANGE_LIMIT_H

#include <stdbool.h>
#include <stddef.h>

/* PERIOD in rules/rate/change_limit.py, seconds from the row before */
#define CHANGE_LIMIT_PERIOD 0.1f

typedef struct {
	size_t signal; /* index in SIGNALS */
	float limit; /* most a signal may move per second */
} ChangeLimit;

/* LIMITS in rules/rate/change_limit.py */
static const ChangeLimit CHANGE_LIMITS[] = {
	{2, 400.0f}, /* actual_engine_torque */
	{13, 250.0f}, /* brake_pedal */
	{0, 2600.0f}, /* engine_speed */
	{14, 10.0f}, /* steering_angle */
	{12, 40.0f}, /* tachograph_speed */
	{5, 40.0f}, /* wheel_speed */
	{15, 0.4f}, /* yaw_rate */
};
#define CHANGE_LIMIT_SIGNALS (sizeof(CHANGE_LIMITS) / sizeof(CHANGE_LIMITS[0]))

/**
 * @brief Check whether a signal moved further from the row before than a tick allows.
 *
 * The C port of rules/rate/change_limit.py.
 *
 * @param[in] row Physical values in the order of SIGNALS.
 * @param[in] previous The row one tick before, all NaN when there is none.
 * @retval true A signal moved faster than its limit. NaN compares false and never does.
 * @retval false Every signal stayed within its limit.
 * @pre @p row and @p previous contain every signal of SIGNALS.
 */
static inline bool change_limit_hits(const float row[], const float previous[])
{
	size_t i;
	float step;

	for(i = 0; i < CHANGE_LIMIT_SIGNALS; i++) {
		step = row[CHANGE_LIMITS[i].signal] - previous[CHANGE_LIMITS[i].signal];
		if(step < 0.0f) {
			step = -step;
		}
		if(step / CHANGE_LIMIT_PERIOD > CHANGE_LIMITS[i].limit) {
			return true;
		}
	}
	return false;
}

#endif
