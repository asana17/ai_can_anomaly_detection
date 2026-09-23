#ifndef BOARD_RULE_HITS_H
#define BOARD_RULE_HITS_H

#include <stdbool.h>

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

/* the index of each signal in SIGNALS, preprocess/features/signal_state.py */
#define RULE_ENGINE_SPEED 0
#define RULE_DRIVER_DEMAND_TORQUE 1
#define RULE_ACTUAL_ENGINE_TORQUE 2
#define RULE_ACCEL_PEDAL 3
#define RULE_ENGINE_LOAD 4
#define RULE_WHEEL_SPEED 5
#define RULE_FUEL_RATE 6
#define RULE_OUTPUT_SHAFT_SPEED 7
#define RULE_CLUTCH_SLIP 8
#define RULE_INPUT_SHAFT_SPEED 9
#define RULE_SELECTED_GEAR 10
#define RULE_CURRENT_GEAR 11
#define RULE_TACHOGRAPH_SPEED 12
#define RULE_BRAKE_PEDAL 13
#define RULE_STEERING_ANGLE 14
#define RULE_YAW_RATE 15

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
		|| speed_agreement_hits(row[RULE_WHEEL_SPEED], row[RULE_TACHOGRAPH_SPEED])
		|| shaft_ratio_hits(row[RULE_OUTPUT_SHAFT_SPEED], row[RULE_WHEEL_SPEED],
			SHAFT_RATIO_MIN_SPEED)
		|| gear_ratio_hits(row[RULE_ENGINE_SPEED], row[RULE_WHEEL_SPEED],
			row[RULE_CURRENT_GEAR], row[RULE_SELECTED_GEAR],
			row[RULE_CLUTCH_SLIP], min_speed)
		|| steering_sign_hits(row[RULE_STEERING_ANGLE], row[RULE_YAW_RATE],
			row[RULE_WHEEL_SPEED], min_speed)
		|| engine_off_hits(row[RULE_ENGINE_SPEED], row[RULE_FUEL_RATE],
			row[RULE_ACTUAL_ENGINE_TORQUE], row[RULE_ENGINE_LOAD],
			row[RULE_DRIVER_DEMAND_TORQUE], row[RULE_ACCEL_PEDAL],
			row[RULE_INPUT_SHAFT_SPEED])
		|| pedal_conflict_hits(row[RULE_ACCEL_PEDAL], row[RULE_BRAKE_PEDAL])
		|| stopped_shaft_hits(row[RULE_WHEEL_SPEED], row[RULE_OUTPUT_SHAFT_SPEED])
		|| reverse_speed_hits(row[RULE_CURRENT_GEAR], row[RULE_WHEEL_SPEED])
		|| reserved_moving_hits(row, row[RULE_WHEEL_SPEED], row[RULE_TACHOGRAPH_SPEED]);
}

#endif
