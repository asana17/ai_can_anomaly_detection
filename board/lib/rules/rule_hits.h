#ifndef BOARD_RULE_HITS_H
#define BOARD_RULE_HITS_H

#include <stdbool.h>
#include "signals.h"
#include "engine_off.h"
#include "gear_ratio.h"
#include "pedal_conflict.h"
#include "range_check.h"
#include "reserved_moving.h"
#include "reverse_speed.h"
#include "shaft_ratio.h"
#include "speed_agreement.h"
#include "steering_sign.h"
#include "stopped_shaft.h"

/**
 * @brief Check whether an instant rule hits a row.
 *
 * The C port of `rule_hits` in rules/hits.py, in the order `instant` lists the rules.
 *
 * @param[in] row Physical values in the order of SIGNALS.
 * @param[in] min_speed Wheel speed in km/h the moving rules start at, Settings.MIN_SPEED.
 * @retval true A rule hits the row.
 * @retval false None of them does.
 * @pre @p row contains RANGE_CHECK_SIGNALS elements.
 */
static inline bool rule_hits(const float row[], float min_speed)
{
	return range_check_hits(row)
		|| speed_agreement_hits(row[SIGNAL_WHEEL_SPEED], row[SIGNAL_TACHOGRAPH_SPEED])
		|| shaft_ratio_hits(row[SIGNAL_OUTPUT_SHAFT_SPEED], row[SIGNAL_WHEEL_SPEED],
			SHAFT_RATIO_MIN_SPEED)
		|| gear_ratio_hits(row[SIGNAL_ENGINE_SPEED], row[SIGNAL_WHEEL_SPEED],
			row[SIGNAL_CURRENT_GEAR], row[SIGNAL_SELECTED_GEAR],
			row[SIGNAL_CLUTCH_SLIP], min_speed)
		|| steering_sign_hits(row[SIGNAL_STEERING_ANGLE], row[SIGNAL_YAW_RATE],
			row[SIGNAL_WHEEL_SPEED], min_speed)
		|| engine_off_hits(row[SIGNAL_ENGINE_SPEED], row[SIGNAL_FUEL_RATE],
			row[SIGNAL_ACTUAL_ENGINE_TORQUE], row[SIGNAL_ENGINE_LOAD],
			row[SIGNAL_DRIVER_DEMAND_TORQUE], row[SIGNAL_ACCEL_PEDAL])
		|| pedal_conflict_hits(row[SIGNAL_ACCEL_PEDAL], row[SIGNAL_BRAKE_PEDAL])
		|| stopped_shaft_hits(row[SIGNAL_WHEEL_SPEED], row[SIGNAL_TACHOGRAPH_SPEED],
			row[SIGNAL_OUTPUT_SHAFT_SPEED])
		|| reverse_speed_hits(row[SIGNAL_CURRENT_GEAR], row[SIGNAL_WHEEL_SPEED])
		|| reserved_moving_hits(row, row[SIGNAL_WHEEL_SPEED], row[SIGNAL_TACHOGRAPH_SPEED],
			row[SIGNAL_OUTPUT_SHAFT_SPEED]);
}

#endif
