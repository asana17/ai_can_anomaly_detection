#include <stddef.h>
#include "gear_ratio.h"

typedef struct {
	float gear;
	float ratio;
} GearRatio;

/* RATIOS in rules/instant/gear_ratio.py */
static const GearRatio RATIOS[] = {
	{2.0f, 179.25f}, {4.0f, 108.69f}, {5.0f, 87.02f}, {6.0f, 67.20f},
	{7.0f, 52.27f}, {8.0f, 41.37f}, {9.0f, 31.69f}, {10.0f, 24.82f},
	{11.0f, 19.37f}, {12.0f, 15.24f},
};
#define GEARS (sizeof(RATIOS) / sizeof(RATIOS[0]))

static bool in_table(float gear)
{
	size_t i;

	for(i = 0; i < GEARS; i++) {
		if(RATIOS[i].gear == gear) {
			return true;
		}
	}
	return false;
}

/* The gear whose ratio is closest to `ratio`, compared as a proportion. */
static float nearest_gear(float ratio)
{
	size_t i, best = 0;
	float distance, best_distance = 0.0f;

	for(i = 0; i < GEARS; i++) {
		distance = RATIOS[i].ratio / ratio;
		if(ratio / RATIOS[i].ratio > distance) {
			distance = ratio / RATIOS[i].ratio;
		}
		if(i == 0 || distance < best_distance) {
			best = i;
			best_distance = distance;
		}
	}
	return RATIOS[best].gear;
}

bool gear_ratio_hits(float engine_speed, float wheel_speed, float current_gear,
	float selected_gear, float clutch_slip, float min_speed)
{
	/* mid shift or with the clutch open there is no fixed ratio */
	if(wheel_speed < min_speed || !in_table(current_gear)
		|| current_gear != selected_gear || clutch_slip != 0.0f) {
		return false;
	}
	/* the closed clutch turns the engine with the wheels, so a stopped engine
	 * contradicts the speed above */
	if(engine_speed <= 0.0f) {
		return true;
	}
	return nearest_gear(engine_speed / wheel_speed) != current_gear;
}
