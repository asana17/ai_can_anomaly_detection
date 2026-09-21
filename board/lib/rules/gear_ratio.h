#ifndef BOARD_GEAR_RATIO_H
#define BOARD_GEAR_RATIO_H

#include <stdbool.h>

/**
 * @brief Check whether the engine and wheel speeds pick out the reported gear.
 *
 * The C port of rules/instant/gear_ratio.py.
 *
 * @param[in] engine_speed Engine speed in rpm.
 * @param[in] wheel_speed Wheel-based vehicle speed in km/h.
 * @param[in] current_gear Gear the transmission reports.
 * @param[in] selected_gear Gear the transmission is shifting to.
 * @param[in] clutch_slip Clutch slip in percent.
 * @param[in] min_speed Wheel speed in km/h below which the rule stays quiet.
 * @retval true The speeds pick out another gear, or the engine is stopped in gear.
 * @retval false The speeds match, or the rule cannot tell.
 */
bool gear_ratio_hits(float engine_speed, float wheel_speed, float current_gear,
	float selected_gear, float clutch_slip, float min_speed);

#endif
