#ifndef BOARD_SPN_SPEC_H
#define BOARD_SPN_SPEC_H

#include <stddef.h>
#include <stdint.h>

#include "spn_decode.h"

typedef struct {
	uint32_t pgn;
	SpnField field;
} SpnDef;

/* SPEC in preprocess/frames/spn_spec.py, in the order of SIGNALS */
static const SpnDef SPN_SPEC[] = {
	{61444u, {24, 16, 0.125f, 0.0f}}, /* EEC1 engine_speed */
	{61444u, {8, 8, 1.0f, -125.0f}}, /* EEC1 driver_demand_torque */
	{61444u, {16, 8, 1.0f, -125.0f}}, /* EEC1 actual_engine_torque */
	{61443u, {8, 8, 0.4f, 0.0f}}, /* EEC2 accel_pedal */
	{61443u, {16, 8, 1.0f, 0.0f}}, /* EEC2 engine_load */
	{65265u, {8, 16, 0.00390625f, 0.0f}}, /* CCVS1 wheel_speed */
	{65266u, {0, 16, 0.05f, 0.0f}}, /* LFE1 fuel_rate */
	{61442u, {8, 16, 0.125f, 0.0f}}, /* ETC1 output_shaft_speed */
	{61442u, {24, 8, 0.4f, 0.0f}}, /* ETC1 clutch_slip */
	{61442u, {40, 16, 0.125f, 0.0f}}, /* ETC1 input_shaft_speed */
	{61445u, {0, 8, 1.0f, -125.0f}}, /* ETC2 selected_gear */
	{61445u, {24, 8, 1.0f, -125.0f}}, /* ETC2 current_gear */
	{65132u, {48, 16, 1.0f / 256, 0.0f}}, /* TCO1 tachograph_speed */
	{61441u, {8, 8, 0.4f, 0.0f}}, /* EBC1 brake_pedal */
	{61449u, {0, 16, 1.0f / 1024, -31.374f}}, /* VDC2 steering_angle */
	{61449u, {24, 16, 1.0f / 8192, -3.92f}}, /* VDC2 yaw_rate */
	{61449u, {40, 16, 1.0f / 2048, -15.687f}}, /* VDC2 lateral_accel */
};
#define SPN_SPEC_SIGNALS (sizeof(SPN_SPEC) / sizeof(SPN_SPEC[0]))

#endif
