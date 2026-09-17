/**
 * grid_sample.c — Resample a CAN frame stream onto a fixed-period time grid.
 *
 * Port of preprocess/features/grid_sample.py.
 *
 * Python generator loop (annotated):
 *
 *   state = SignalState()
 *   next_tick = None
 *   previous = None
 *   for f in frames:
 *       pgn = decompose_can_id(f.can_id).pgn
 *       # (1) gap detection
 *       if previous is not None and f.timestamp - previous > max_hold:
 *           state = SignalState()      # drop stale values
 *           next_tick = None           # restart the grid
 *       # (2) emit all ticks that elapsed before this frame
 *       while next_tick is not None and f.timestamp >= next_tick:
 *           if state.ready():
 *               yield (next_tick, state.row())
 *           next_tick += period
 *       # (3) update hold-last with this frame's signals
 *       state.update(decode_frame(pgn, f.data))
 *       previous = f.timestamp
 *       # (4) arm the grid on the first frame
 *       if next_tick is None:
 *           next_tick = f.timestamp + period
 *
 * The C translation replaces the epoch-second float timestamps with uint32_t
 * milliseconds.  Unsigned subtraction handles the 49-day HAL_GetTick()
 * wraparound transparently.
 */
#include "grid_sample.h"
#include "can_id.h"
#include "frame_decode.h"

#include <math.h>    /* NAN */
#include <string.h>  /* memset */

void grid_sampler_init(GridSampler *g, uint32_t period_ms, uint32_t max_hold_ms,
                       RowCallback on_row)
{
    signal_state_init(&g->state);
    g->next_tick_ms = 0u;
    g->prev_ms      = 0u;
    g->period_ms    = period_ms;
    g->max_hold_ms  = max_hold_ms;
    g->on_row       = on_row;
    g->started      = false;
}

void grid_feed(GridSampler *g, uint32_t arb_id, const uint8_t *data,
               uint8_t dlc, uint32_t now_ms)
{
    /* (1) Gap detection.
     *
     * Unsigned subtraction wraps correctly; a gap of 2^32-1 ms is ~49 days,
     * which will never occur in practice.  We only check once started, to
     * avoid a spurious reset before the first frame.
     */
    if (g->started && (now_ms - g->prev_ms) > g->max_hold_ms) {
        signal_state_init(&g->state);   /* drop stale held values */
        g->started = false;             /* re-arm the grid */
    }

    /* (2) Emit all grid ticks that have elapsed since the last frame.
     *
     * The while condition mirrors Python's:
     *   while next_tick is not None and f.timestamp >= next_tick
     *
     * In C: `started` plays the role of "next_tick is not None".
     * Unsigned comparison: if now_ms < next_tick_ms the subtraction would
     * wrap; testing (now_ms - next_tick_ms) < 0x80000000u is a clean way to
     * check "now_ms >= next_tick_ms" without signed overflow.  However, since
     * we know the gap is at most max_hold_ms (≤ a few seconds), a simple
     * signed-safe compare suffices: cast to int32_t.
     */
    while (g->started && (int32_t)(now_ms - g->next_tick_ms) >= 0) {
        if (signal_state_ready(&g->state)) {
            float row[NUM_SIGNALS];
            signal_state_row(&g->state, row);
            g->on_row(row, g->next_tick_ms);
        }
        g->next_tick_ms += g->period_ms;
    }

    /* (3) Decode this frame and update the hold-last state.
     *
     * incoming is initialised to all-NAN so that only slots belonging to
     * this PGN are written, and frame_decode skips NA fields by leaving
     * them as NAN.  signal_state_update then only overwrites non-NAN slots.
     */
    uint32_t pgn = can_id_decompose(arb_id).pgn;
    float incoming[NUM_SIGNALS];
    for (uint8_t i = 0u; i < NUM_SIGNALS; i++)
        incoming[i] = NAN;
    frame_decode(pgn, data, dlc, incoming);
    signal_state_update(&g->state, incoming);

    g->prev_ms = now_ms;

    /* (4) Arm the grid on the very first frame. */
    if (!g->started) {
        g->next_tick_ms = now_ms + g->period_ms;
        g->started = true;
    }
}
