#ifndef BOARD_CHANGE_LIMIT_H
#define BOARD_CHANGE_LIMIT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "recent_rows.h"

/* PERIOD in rules/sequence/change_limit.py, seconds from the row before */
#define CHANGE_LIMIT_PERIOD 0.1f

typedef struct {
	size_t signal; /* index in SIGNALS */
	float limit; /* most a signal may move per second */
} ChangeLimit;

/* LIMITS in rules/sequence/change_limit.py */
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
 * The C port of rules/sequence/change_limit.py.
 *
 * @param[in] recent The rows before @p row since a gap.
 * @param[in] row Physical values in the order of SIGNALS.
 * @retval true A signal moved faster than its limit. NaN compares false and never does.
 * @retval false Every signal stayed within its limit, or @p recent holds no row.
 */
static inline bool change_limit_hits(const RecentRows *recent, const float row[])
{
	uint32_t held = recent_rows_count(recent);
	const float *previous;
	size_t i;
	float step;

	if (held == 0u) {
		return false;
	}
	previous = recent_rows_row(recent, held - 1u);
	for (i = 0; i < CHANGE_LIMIT_SIGNALS; i++) {
		step = row[CHANGE_LIMITS[i].signal] - previous[CHANGE_LIMITS[i].signal];
		if (step < 0.0f) {
			step = -step;
		}
		if (step / CHANGE_LIMIT_PERIOD > CHANGE_LIMITS[i].limit) {
			return true;
		}
	}
	return false;
}

#endif
