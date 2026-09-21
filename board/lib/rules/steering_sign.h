#ifndef BOARD_STEERING_SIGN_H
#define BOARD_STEERING_SIGN_H

#include <stdbool.h>

/* MIN_YAW in rules/instant/steering_sign.py */
#define STEERING_SIGN_MIN_YAW 0.02f

/**
 * @brief Check whether the steering angle and the yaw rate turn the same way.
 *
 * The C port of rules/instant/steering_sign.py.
 *
 * @param[in] steering_angle Steering wheel angle in rad.
 * @param[in] yaw_rate Yaw rate in rad/s.
 * @param[in] wheel_speed Wheel-based vehicle speed in km/h.
 * @param[in] min_speed Wheel speed in km/h below which the rule stays quiet.
 * @retval true The wheel is turned one way and the truck turns the other.
 * @retval false They agree, or the truck is slow or going straight.
 */
static inline bool steering_sign_hits(float steering_angle, float yaw_rate,
	float wheel_speed, float min_speed)
{
	/* below MIN_YAW the truck is going straight and the sign is noise */
	if(!(wheel_speed >= min_speed) || !(yaw_rate >= STEERING_SIGN_MIN_YAW
		|| -yaw_rate >= STEERING_SIGN_MIN_YAW)) {
		return false;
	}
	return (steering_angle > 0.0f) != (yaw_rate > 0.0f);
}

#endif
