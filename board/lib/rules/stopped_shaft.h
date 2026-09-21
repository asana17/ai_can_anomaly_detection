#ifndef BOARD_STOPPED_SHAFT_H
#define BOARD_STOPPED_SHAFT_H

#include <stdbool.h>

/* MAX_SHAFT in rules/instant/stopped_shaft.py */
#define STOPPED_SHAFT_MAX_SHAFT 50.0f

/**
 * @brief Check whether the output shaft turns with the wheels stopped.
 *
 * The C port of rules/instant/stopped_shaft.py.
 *
 * @param[in] wheel_speed Wheel-based vehicle speed in km/h.
 * @param[in] output_shaft_speed Transmission output shaft speed in rpm.
 * @retval true The wheels read zero and the shaft is above STOPPED_SHAFT_MAX_SHAFT.
 * @retval false Otherwise.
 */
static inline bool stopped_shaft_hits(float wheel_speed, float output_shaft_speed)
{
	return wheel_speed == 0.0f && output_shaft_speed > STOPPED_SHAFT_MAX_SHAFT;
}

#endif
