/**
 * grid_sample.h — Resample a CAN frame stream onto a fixed-period time grid.
 *
 * Port of preprocess/features/grid_sample.py.
 *
 * The Python implementation is a generator that iterates over a list of
 * frames.  On the board, frames arrive one at a time from the CAN peripheral,
 * so this port is event-driven: the caller feeds frames via grid_feed() and
 * provides a callback that is invoked whenever a complete row is ready.
 *
 * Timing is in milliseconds (uint32_t), matching HAL_GetTick().  Unsigned
 * 32-bit subtraction handles the ~49-day wraparound correctly for gaps that
 * are at most a few hours.
 *
 * Example usage (bare-metal, called from CAN RX ISR or task):
 *
 *   static GridSampler g;
 *
 *   void on_row(const float row[NUM_SIGNALS], uint32_t tick_ms) {
 *       // hand row to the anomaly-detection model
 *   }
 *
 *   void app_init(void) {
 *       grid_sampler_init(&g, 100, 1000, on_row);
 *   }
 *
 *   void CAN_RX_IRQHandler(void) {
 *       uint32_t id; uint8_t data[8]; uint8_t dlc;
 *       // ... read from HAL ...
 *       grid_feed(&g, id, data, dlc, HAL_GetTick());
 *   }
 */
#ifndef GRID_SAMPLE_H
#define GRID_SAMPLE_H

#include "signal_state.h"
#include <stdbool.h>
#include <stdint.h>

/**
 * Called by grid_feed() each time a complete row is produced.
 *
 * @param row      NUM_SIGNALS floats in SIGNALS order.
 * @param tick_ms  Grid tick timestamp in milliseconds.
 */
typedef void (*RowCallback)(const float row[NUM_SIGNALS], uint32_t tick_ms);

/** All state for one grid resampler instance. */
typedef struct {
    SignalState  state;         /**< Hold-last signal values. */
    uint32_t     next_tick_ms;  /**< Timestamp of the next grid tick to emit. */
    uint32_t     prev_ms;       /**< Timestamp of the most recent frame seen. */
    uint32_t     period_ms;     /**< Grid period, e.g. 100 for 10 Hz. */
    uint32_t     max_hold_ms;   /**< Longest gap the grid carries across, e.g. 1000. */
    RowCallback  on_row;        /**< Callback invoked for each complete row. */
    bool         started;       /**< False until the first frame has been seen. */
} GridSampler;

/**
 * Initialise a GridSampler.
 *
 * @param g            Sampler to initialise.
 * @param period_ms    Emit one row every this many milliseconds (e.g. 100).
 * @param max_hold_ms  Reset the grid if frames stop for this long (e.g. 1000).
 * @param on_row       Callback invoked whenever a row is ready; must not be NULL.
 */
void grid_sampler_init(GridSampler *g, uint32_t period_ms, uint32_t max_hold_ms,
                       RowCallback on_row);

/**
 * Feed one CAN frame into the resampler.
 *
 * May call on_row zero or more times synchronously before returning.
 * Zero times is normal when signals have not all arrived yet, or when
 * no tick has elapsed since the last frame.  More than one tick can fire
 * if frames are delayed (e.g. by interrupt latency).
 *
 * @param g       Sampler instance.
 * @param arb_id  Raw 29-bit J1939 arbitration ID.
 * @param data    Payload bytes.
 * @param dlc     Number of valid bytes in data (≤ 8).
 * @param now_ms  Current HAL_GetTick() value.
 */
void grid_feed(GridSampler *g, uint32_t arb_id, const uint8_t *data,
               uint8_t dlc, uint32_t now_ms);

#endif /* GRID_SAMPLE_H */
