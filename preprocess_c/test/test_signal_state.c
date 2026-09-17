/**
 * test_signal_state.c — Unit tests for SignalState.
 *
 * Compile & run:
 *   make test_signal_state && ./test_signal_state
 */
#include "../signal_state.h"
#include "../spn_spec.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    SignalState s;
    float incoming[NUM_SIGNALS];
    float row[NUM_SIGNALS];

    /* --- init: all NAN, not ready --- */
    signal_state_init(&s);
    assert(!signal_state_ready(&s));
    for (uint8_t i = 0; i < NUM_SIGNALS; i++)
        assert(isnan(s.values[i]));
    printf("PASS  init: all NAN, not ready\n");

    /* --- update with all-NAN incoming changes nothing --- */
    for (uint8_t i = 0; i < NUM_SIGNALS; i++) incoming[i] = NAN;
    signal_state_update(&s, incoming);
    assert(!signal_state_ready(&s));
    printf("PASS  update all-NAN → still not ready\n");

    /* --- update sets only the non-NAN slots --- */
    for (uint8_t i = 0; i < NUM_SIGNALS; i++) incoming[i] = NAN;
    incoming[0] = 800.0f;   /* engine_speed */
    incoming[5] = 60.0f;    /* wheel_speed */
    signal_state_update(&s, incoming);
    assert(!isnan(s.values[0]));
    assert(s.values[0] == 800.0f);
    assert(!isnan(s.values[5]));
    assert(s.values[5] == 60.0f);
    assert(isnan(s.values[1]));  /* still unseen */
    assert(!signal_state_ready(&s));
    printf("PASS  partial update sets correct slots\n");

    /* --- fill all signals → ready --- */
    for (uint8_t i = 0; i < NUM_SIGNALS; i++) incoming[i] = (float)i;
    signal_state_update(&s, incoming);
    assert(signal_state_ready(&s));
    printf("PASS  all slots filled → ready\n");

    /* --- row copies all values --- */
    signal_state_row(&s, row);
    for (uint8_t i = 0; i < NUM_SIGNALS; i++)
        assert(row[i] == s.values[i]);
    printf("PASS  signal_state_row copies all values\n");

    /* --- update overwrites only non-NAN slots, leaves others intact --- */
    for (uint8_t i = 0; i < NUM_SIGNALS; i++) incoming[i] = NAN;
    incoming[3] = 42.5f;  /* accel_pedal */
    signal_state_update(&s, incoming);
    assert(s.values[3] == 42.5f);
    assert(s.values[0] == 0.0f);   /* set from previous update, unchanged */
    printf("PASS  update with partial incoming preserves other slots\n");

    /* --- init resets to NAN / not-ready --- */
    signal_state_init(&s);
    assert(!signal_state_ready(&s));
    for (uint8_t i = 0; i < NUM_SIGNALS; i++)
        assert(isnan(s.values[i]));
    printf("PASS  re-init resets all to NAN\n");

    printf("\nAll signal_state tests passed.\n");
    return 0;
}
