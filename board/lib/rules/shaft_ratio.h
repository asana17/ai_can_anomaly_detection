#ifndef BOARD_SHAFT_RATIO_H
#define BOARD_SHAFT_RATIO_H

#include <stdbool.h>

/* BOUNDS in rules/instant/shaft_ratio.py */
#define SHAFT_RATIO_LOWER 13.0f
#define SHAFT_RATIO_UPPER 17.5f
/* MIN_SPEED in rules/instant/shaft_ratio.py */
#define SHAFT_RATIO_MIN_SPEED 20.0f

/**
 * @brief Check whether the output shaft turns at the right rate for the wheel speed.
 *
 * The C port of rules/instant/shaft_ratio.py.
 *
 * @param[in] output_shaft_speed Transmission output shaft speed in rpm.
 * @param[in] wheel_speed Wheel-based vehicle speed in km/h.
 * @param[in] min_speed Wheel speed in km/h below which the rule stays quiet.
 * @retval true The ratio of the two is outside the measured bounds.
 * @retval false The ratio is inside them, or the wheel is below @p min_speed.
 */
static inline bool shaft_ratio_hits(float output_shaft_speed, float wheel_speed,
	float min_speed)
{
	float ratio;

	if(!(wheel_speed >= min_speed)) {
		return false;
	}
	ratio = output_shaft_speed / wheel_speed;
	return ratio < SHAFT_RATIO_LOWER || ratio > SHAFT_RATIO_UPPER;
}

#endif
