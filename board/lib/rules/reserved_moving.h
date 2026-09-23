#ifndef BOARD_RESERVED_MOVING_H
#define BOARD_RESERVED_MOVING_H

#include <math.h>
#include <stdbool.h>
#include <stddef.h>

/* len(SIGNALS) in preprocess/features/signal_state.py */
#define RESERVED_MOVING_SIGNALS 17

/**
 * @brief Check whether a signal is reserved, NaN, while the truck moves.
 *
 * The C port of rules/instant/reserved_moving.py.
 *
 * @param[in] row Physical values in the order of SIGNALS.
 * @param[in] wheel_speed Wheel-based vehicle speed in km/h.
 * @param[in] tachograph_speed Tachograph vehicle speed in km/h.
 * @retval true A signal is NaN and either speed is above 0.
 * @retval false Otherwise.
 * @pre @p row contains RESERVED_MOVING_SIGNALS elements.
 */
static inline bool reserved_moving_hits(const float row[], float wheel_speed,
	float tachograph_speed)
{
	size_t i;

	if(!(wheel_speed > 0.0f || tachograph_speed > 0.0f)) {
		return false;
	}
	for(i = 0; i < RESERVED_MOVING_SIGNALS; i++) {
		if(isnan(row[i])) {
			return true;
		}
	}
	return false;
}

#endif
