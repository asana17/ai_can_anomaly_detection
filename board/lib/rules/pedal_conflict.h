#ifndef BOARD_PEDAL_CONFLICT_H
#define BOARD_PEDAL_CONFLICT_H

#include <stdbool.h>

/* PRESSED in rules/instant/pedal_conflict.py */
#define PEDAL_CONFLICT_PRESSED 10.0f

/**
 * @brief Check whether the accelerator and the brake are pressed at once.
 *
 * The C port of rules/instant/pedal_conflict.py.
 *
 * @param[in] accel_pedal Accelerator pedal position in percent.
 * @param[in] brake_pedal Brake pedal position in percent.
 * @retval true Both are above PEDAL_CONFLICT_PRESSED.
 * @retval false Otherwise.
 */
static inline bool pedal_conflict_hits(float accel_pedal, float brake_pedal)
{
	return accel_pedal > PEDAL_CONFLICT_PRESSED && brake_pedal > PEDAL_CONFLICT_PRESSED;
}

#endif
