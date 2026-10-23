#ifndef BOARD_MOVING_H
#define BOARD_MOVING_H

#include <stdbool.h>

#define MOVING_WHEEL_SPEED 5 /* SIGNALS.index("wheel_speed") */

/**
 * @brief Check whether a row's wheel speed is above a given speed.
 *
 * The C port of preprocess/features/moving.py.
 *
 * @param[in] row Physical values in the order of SIGNALS.
 * @param[in] min_speed The speed in km/h the wheel speed has to exceed.
 * @retval true The wheel speed is above @p min_speed.
 * @retval false It is not, or it is NaN.
 */
static inline bool moving(const float row[], float min_speed)
{
	return row[MOVING_WHEEL_SPEED] > min_speed;
}

#endif
