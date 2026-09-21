#ifndef BOARD_SPEED_AGREEMENT_H
#define BOARD_SPEED_AGREEMENT_H

#include <stdbool.h>

/* MAX_DISAGREEMENT in rules/instant/speed_agreement.py */
#define SPEED_AGREEMENT_LIMIT 2.0f

/**
 * @brief Check whether the wheel and tachograph speeds agree.
 *
 * The C port of rules/instant/speed_agreement.py.
 *
 * @param[in] wheel_speed Wheel-based vehicle speed in km/h.
 * @param[in] tachograph_speed Tachograph vehicle speed in km/h.
 * @retval true The two differ by more than SPEED_AGREEMENT_LIMIT.
 * @retval false They agree.
 */
static inline bool speed_agreement_hits(float wheel_speed, float tachograph_speed)
{
	float difference = wheel_speed - tachograph_speed;

	if(difference < 0.0f) {
		difference = -difference;
	}
	return difference > SPEED_AGREEMENT_LIMIT;
}

#endif
