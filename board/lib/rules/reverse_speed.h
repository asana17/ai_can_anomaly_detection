#ifndef BOARD_REVERSE_SPEED_H
#define BOARD_REVERSE_SPEED_H

#include <stdbool.h>

/* MAX_SPEED in rules/instant/reverse_speed.py */
#define REVERSE_SPEED_MAX_SPEED 10.0f

/**
 * @brief Check whether reverse is engaged above a speed reverse cannot reach.
 *
 * The C port of rules/instant/reverse_speed.py.
 *
 * @param[in] current_gear Gear the transmission reports, negative in reverse.
 * @param[in] wheel_speed Wheel-based vehicle speed in km/h.
 * @retval true Reverse above REVERSE_SPEED_MAX_SPEED.
 * @retval false Otherwise.
 */
static inline bool reverse_speed_hits(float current_gear, float wheel_speed)
{
	return current_gear < 0.0f && wheel_speed > REVERSE_SPEED_MAX_SPEED;
}

#endif
