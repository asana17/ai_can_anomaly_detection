#ifndef BOARD_ENGINE_OFF_H
#define BOARD_ENGINE_OFF_H

#include <stdbool.h>

/**
 * @brief Check whether anything the engine drives runs while the engine is stopped.
 *
 * The C port of rules/instant/engine_off.py. The six after @p engine_speed are its
 * MUST_BE_ZERO.
 *
 * @param[in] engine_speed Engine speed in rpm.
 * @param[in] fuel_rate Fuel rate in L/h.
 * @param[in] actual_engine_torque Actual engine torque in percent.
 * @param[in] engine_load Engine load in percent.
 * @param[in] driver_demand_torque Driver demand torque in percent.
 * @param[in] accel_pedal Accelerator pedal position in percent.
 * @param[in] input_shaft_speed Transmission input shaft speed in rpm.
 * @retval true The engine reads zero and one of the others does not.
 * @retval false Otherwise.
 */
static inline bool engine_off_hits(float engine_speed, float fuel_rate,
	float actual_engine_torque, float engine_load, float driver_demand_torque,
	float accel_pedal, float input_shaft_speed)
{
	return engine_speed == 0.0f && (fuel_rate != 0.0f || actual_engine_torque != 0.0f
		|| engine_load != 0.0f || driver_demand_torque != 0.0f
		|| accel_pedal != 0.0f || input_shaft_speed != 0.0f);
}

#endif
