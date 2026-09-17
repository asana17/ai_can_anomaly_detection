/**
 * signal_state.h — Hold-last state for all 17 tracked signals.
 *
 * Port of preprocess/features/signal_state.py.
 *
 * Each slot is NAN until the first frame for that signal arrives.
 * signal_state_ready() returns true once all 17 slots are filled.
 */
#ifndef SIGNAL_STATE_H
#define SIGNAL_STATE_H

#include "spn_spec.h"
#include <stdbool.h>

/**
 * Hold-last buffer for one complete signal row.
 *
 * values[i] is NAN while signal i has not yet been seen.
 */
typedef struct {
    float values[NUM_SIGNALS];
} SignalState;

/**
 * Initialise (or re-initialise) a SignalState to all-NAN.
 * Call this at startup and after a gap resets the grid.
 */
void signal_state_init(SignalState *s);

/**
 * Write non-NAN slots from `incoming` into the state.
 *
 * Mirrors Python update(): only signals present in the decoded frame
 * (i.e. not NAN in `incoming`) overwrite the held value.
 *
 * @param s        State to update.
 * @param incoming Array of NUM_SIGNALS floats, NAN for absent signals.
 */
void signal_state_update(SignalState *s, const float incoming[NUM_SIGNALS]);

/**
 * True once every signal has been seen at least once.
 * Matches Python ready().
 */
bool signal_state_ready(const SignalState *s);

/**
 * Copy the current state into `row`.
 * Only call when signal_state_ready() is true.
 */
void signal_state_row(const SignalState *s, float row[NUM_SIGNALS]);

#endif /* SIGNAL_STATE_H */
