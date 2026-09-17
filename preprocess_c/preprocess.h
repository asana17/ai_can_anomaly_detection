/**
 * preprocess.h — Single public header for the preprocess C library.
 *
 * Board firmware only needs to include this one header.
 *
 * Typical bare-metal usage:
 *
 *   #include "preprocess.h"
 *
 *   static GridSampler g;
 *
 *   static void on_row(const float row[NUM_SIGNALS], uint32_t tick_ms) {
 *       // feed row[0..16] to the anomaly detection model
 *   }
 *
 *   void app_init(void) {
 *       grid_sampler_init(&g, 100, 1000, on_row);
 *   }
 *
 *   // Called from CAN RX interrupt or RTOS task:
 *   void on_can_frame(uint32_t arb_id, uint8_t *data, uint8_t dlc) {
 *       grid_feed(&g, arb_id, data, dlc, HAL_GetTick());
 *   }
 */
#ifndef PREPROCESS_H
#define PREPROCESS_H

#include "can_id.h"
#include "spn_decode.h"
#include "spn_spec.h"
#include "frame_decode.h"
#include "signal_state.h"
#include "grid_sample.h"

#endif /* PREPROCESS_H */
