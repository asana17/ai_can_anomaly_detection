/**
 * test_spn_decode.c — Unit tests for spn_decode() and spn_spec_lookup().
 *
 * Each test constructs a synthetic 8-byte payload, calls spn_decode(), and
 * checks the result against the expected physical value computed by hand from
 * the Python SpnField definitions.
 *
 * Compile & run:
 *   make test_spn_decode && ./test_spn_decode
 */
#include "../spn_decode.h"
#include "../spn_spec.h"

#include <assert.h>
#include <math.h>    /* fabsf, isnan, NAN */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* Allow 1 ULP of float32 rounding: half an LSB of each SPN's resolution. */
static void check_float(float got, float expected, float tol, const char *label)
{
    assert(!isnan(got));
    float err = fabsf(got - expected);
    if (err > tol) {
        printf("FAIL  %s: got %.6f, expected %.6f, err %.6f > tol %.6f\n",
               label, (double)got, (double)expected, (double)err, (double)tol);
        assert(0);
    }
    printf("PASS  %s  (%.6f)\n", label, (double)got);
}

static void check_nan(float got, const char *label)
{
    assert(isnan(got));
    printf("PASS  %s  (NAN as expected)\n", label);
}

int main(void)
{
    uint8_t payload[8];

    /* ------------------------------------------------------------------
     * SPN 190  engine_speed
     * field: start_bit=24, length=16, scale=0.125, offset=0.0
     * raw bytes at offset 3-4 (little-endian)
     * ------------------------------------------------------------------ */
    /* raw = 0x0400 = 1024 → 1024 * 0.125 + 0 = 128.0 rpm */
    memset(payload, 0, 8);
    payload[3] = 0x00; payload[4] = 0x04;   /* 0x0400 LE = 1024 */
    {
        SpnField f = {24, 16, 0.125f, 0.0f};
        check_float(spn_decode(payload, 8, f), 128.0f, 0.001f,
                    "engine_speed raw=1024 → 128.0 rpm");
    }

    /* raw = 0 → 0.0 rpm (idle / engine off) */
    memset(payload, 0, 8);
    {
        SpnField f = {24, 16, 0.125f, 0.0f};
        check_float(spn_decode(payload, 8, f), 0.0f, 0.0f,
                    "engine_speed raw=0 → 0.0 rpm");
    }

    /* ------------------------------------------------------------------
     * SPN 512  driver_demand_torque
     * field: start_bit=8, length=8, scale=1.0, offset=-125.0
     * raw byte at offset 1
     * ------------------------------------------------------------------ */
    /* raw = 125 → 125 * 1.0 + (-125.0) = 0 % (neutral) */
    memset(payload, 0, 8);
    payload[1] = 125;
    {
        SpnField f = {8, 8, 1.0f, -125.0f};
        check_float(spn_decode(payload, 8, f), 0.0f, 0.0f,
                    "driver_demand_torque raw=125 → 0%");
    }

    /* raw = 225 → 225 - 125 = 100 % */
    memset(payload, 0, 8);
    payload[1] = 225;
    {
        SpnField f = {8, 8, 1.0f, -125.0f};
        check_float(spn_decode(payload, 8, f), 100.0f, 0.001f,
                    "driver_demand_torque raw=225 → 100%");
    }

    /* ------------------------------------------------------------------
     * SPN 91  accel_pedal
     * field: start_bit=8, length=8, scale=0.4, offset=0.0
     * ------------------------------------------------------------------ */
    /* raw = 250 → 250 * 0.4 = 100.0 % (full throttle) */
    memset(payload, 0, 8);
    payload[1] = 250;
    {
        SpnField f = {8, 8, 0.4f, 0.0f};
        check_float(spn_decode(payload, 8, f), 100.0f, 0.001f,
                    "accel_pedal raw=250 → 100%");
    }

    /* ------------------------------------------------------------------
     * SPN 84  wheel_speed  (CCVS1)
     * field: start_bit=8, length=16, scale=0.00390625, offset=0.0
     * raw=0x1900=6400 → 6400/256 = 25.0 km/h
     * ------------------------------------------------------------------ */
    memset(payload, 0, 8);
    payload[1] = 0x00; payload[2] = 0x19;   /* 0x1900 LE = 6400 */
    {
        SpnField f = {8, 16, 0.00390625f, 0.0f};
        check_float(spn_decode(payload, 8, f), 25.0f, 0.001f,
                    "wheel_speed raw=6400 → 25.0 km/h");
    }

    /* ------------------------------------------------------------------
     * SPN 1807  steering_angle  (VDC2)
     * field: start_bit=0, length=16, scale=1/1024, offset=-31.374
     * raw=0x8000=32768 → 32768/1024 - 31.374 = 32.0 - 31.374 = 0.626 rad
     * ------------------------------------------------------------------ */
    memset(payload, 0, 8);
    payload[0] = 0x00; payload[1] = 0x80;   /* 0x8000 LE = 32768 */
    {
        SpnField f = {0, 16, 0.0009765625f, -31.374f};
        check_float(spn_decode(payload, 8, f), 32768.0f * 0.0009765625f - 31.374f, 0.001f,
                    "steering_angle raw=32768");
    }

    /* ------------------------------------------------------------------
     * Not-available marker: top byte = 0xFF → NAN
     * 8-bit field with raw=0xFF
     * ------------------------------------------------------------------ */
    memset(payload, 0, 8);
    payload[1] = 0xFF;
    {
        SpnField f = {8, 8, 1.0f, -125.0f};
        check_nan(spn_decode(payload, 8, f), "8-bit 0xFF → NAN");
    }

    /* 16-bit field with high byte = 0xFF → NAN */
    memset(payload, 0, 8);
    payload[3] = 0x00; payload[4] = 0xFF;
    {
        SpnField f = {24, 16, 0.125f, 0.0f};
        check_nan(spn_decode(payload, 8, f), "16-bit top byte 0xFF → NAN");
    }

    /* Error marker: top byte = 0xFE → NAN */
    memset(payload, 0, 8);
    payload[1] = 0xFE;
    {
        SpnField f = {8, 8, 0.4f, 0.0f};
        check_nan(spn_decode(payload, 8, f), "8-bit 0xFE → NAN");
    }

    /* ------------------------------------------------------------------
     * spn_spec_lookup: check all 9 tracked PGNs are found
     * ------------------------------------------------------------------ */
    uint32_t tracked[] = {61444, 61443, 65265, 65266, 61442, 61445, 65132, 61441, 61449};
    for (int i = 0; i < 9; i++) {
        const PgnEntry *e = spn_spec_lookup(tracked[i]);
        assert(e != NULL);
        assert(e->pgn == tracked[i]);
        printf("PASS  spn_spec_lookup(%u) found\n", (unsigned)tracked[i]);
    }

    /* Unknown PGN → NULL */
    assert(spn_spec_lookup(12345u) == NULL);
    printf("PASS  spn_spec_lookup(12345) → NULL\n");

    /* Total signal count across all PGNs must equal NUM_SIGNALS */
    uint8_t total = 0;
    for (uint8_t i = 0; i < NUM_PGNS; i++)
        total += PGN_TABLE[i].count;
    assert(total == NUM_SIGNALS);
    printf("PASS  total SPN count == NUM_SIGNALS (%u)\n", (unsigned)NUM_SIGNALS);

    printf("\nAll SPN decode tests passed.\n");
    return 0;
}
