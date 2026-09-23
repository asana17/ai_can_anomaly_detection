#ifndef BOARD_RANGE_CHECK_H
#define BOARD_RANGE_CHECK_H

#include <stdbool.h>
#include <stddef.h>

typedef struct {
	float low;
	float high;
} RangeCheckLimit;

/* LIMITS in rules/instant/range_check.py, in the order of SIGNALS */
static const RangeCheckLimit RANGE_CHECK_LIMITS[] = {
	{0.0f, 8031.875f}, /* engine_speed */
	{-125.0f, 125.0f}, /* driver_demand_torque */
	{-125.0f, 125.0f}, /* actual_engine_torque */
	{0.0f, 100.0f}, /* accel_pedal */
	{0.0f, 250.0f}, /* engine_load */
	{0.0f, 250.996f}, /* wheel_speed */
	{0.0f, 3212.75f}, /* fuel_rate */
	{0.0f, 8031.875f}, /* output_shaft_speed */
	{0.0f, 100.0f}, /* clutch_slip */
	{0.0f, 8031.875f}, /* input_shaft_speed */
	{-125.0f, 125.0f}, /* selected_gear */
	{-125.0f, 125.0f}, /* current_gear */
	{0.0f, 250.996f}, /* tachograph_speed */
	{0.0f, 100.0f}, /* brake_pedal */
	{-31.374f, 31.374f}, /* steering_angle */
	{-3.92f, 3.92f}, /* yaw_rate */
	{-15.687f, 15.687f}, /* lateral_accel */
};
#define RANGE_CHECK_SIGNALS (sizeof(RANGE_CHECK_LIMITS) / sizeof(RANGE_CHECK_LIMITS[0]))

/**
 * @brief Check whether every signal of a row sits inside the range J1939 defines.
 *
 * The C port of rules/instant/range_check.py.
 *
 * @param[in] row Physical values in the order of SIGNALS.
 * @retval true A signal is outside its range. NaN compares false and never is.
 * @retval false Every signal is inside its range.
 * @pre @p row contains RANGE_CHECK_SIGNALS elements.
 */
static inline bool range_check_hits(const float row[])
{
	size_t i;

	for(i = 0; i < RANGE_CHECK_SIGNALS; i++) {
		if(row[i] < RANGE_CHECK_LIMITS[i].low || row[i] > RANGE_CHECK_LIMITS[i].high) {
			return true;
		}
	}
	return false;
}

#endif
