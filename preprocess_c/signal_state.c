/**
 * signal_state.c — Hold-last state for all 17 tracked signals.
 *
 * Port of preprocess/features/signal_state.py.
 */
#include "signal_state.h"

#include <math.h>    /* NAN, isnan */
#include <string.h>  /* memcpy */

void signal_state_init(SignalState *s)
{
    for (uint8_t i = 0u; i < NUM_SIGNALS; i++)
        s->values[i] = NAN;
}

void signal_state_update(SignalState *s, const float incoming[NUM_SIGNALS])
{
    for (uint8_t i = 0u; i < NUM_SIGNALS; i++) {
        if (!isnan(incoming[i]))
            s->values[i] = incoming[i];
    }
}

bool signal_state_ready(const SignalState *s)
{
    for (uint8_t i = 0u; i < NUM_SIGNALS; i++) {
        if (isnan(s->values[i]))
            return false;
    }
    return true;
}

void signal_state_row(const SignalState *s, float row[NUM_SIGNALS])
{
    memcpy(row, s->values, NUM_SIGNALS * sizeof(float));
}
