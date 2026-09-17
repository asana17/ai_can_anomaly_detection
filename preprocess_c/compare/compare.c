/**
 * compare.c — Run the same synthetic CAN frames through the C preprocess
 * pipeline and print one row per line (space-separated floats).
 *
 * The frames, timestamps, and expected values are identical to gen_golden.py.
 * run_compare.sh runs both and compares the outputs.
 *
 * Compile & run:
 *   make compare && ./compare
 */
#include "../preprocess.h"

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* ---------------------------------------------------------------------------
 * Callback: print one row in the same format as gen_golden.py
 * --------------------------------------------------------------------------- */

static void on_row(const float row[NUM_SIGNALS], uint32_t tick_ms)
{
    (void)tick_ms;
    for (uint8_t i = 0u; i < NUM_SIGNALS; i++) {
        if (i) putchar(' ');
        printf("%.6f", (double)row[i]);
    }
    putchar('\n');
}

/* ---------------------------------------------------------------------------
 * Synthetic frames — identical payloads to gen_golden.py
 *
 * Arbitration IDs:  arb_id = (priority<<26) | (pgn<<8) | sa
 *   All priority=6, sa=0xE6, except CCVS1 which uses sa=0x21.
 *
 * Timestamps in milliseconds (vs epoch seconds in Python).
 * --------------------------------------------------------------------------- */

typedef struct { uint32_t now_ms; uint32_t arb_id; uint8_t data[8]; } Frame;

static const Frame FRAMES[] = {
    /* ---- t = 0 ms: seed every signal ---- */

    /* EEC1  PGN 61444  arb_id 0x18F004E6
     * bytes[1]=0xAF  driver_demand_torque  raw=175 → 175-125 =  50 %
     * bytes[2]=0xB9  actual_engine_torque  raw=185 → 185-125 =  60 %
     * bytes[3-4]=0x803E LE  engine_speed  raw=16000 → 16000*0.125 = 2000 rpm */
    {0, 0x18F004E6, {0x00, 0xAF, 0xB9, 0x80, 0x3E, 0x00, 0x00, 0x00}},

    /* EEC2  PGN 61443  arb_id 0x18F003E6
     * bytes[1]=0x4B  accel_pedal  raw=75 → 75*0.4 = 30 %
     * bytes[2]=0x28  engine_load  raw=40 → 40*1.0 = 40 %  */
    {0, 0x18F003E6, {0x00, 0x4B, 0x28, 0x00, 0x00, 0x00, 0x00, 0x00}},

    /* CCVS1  PGN 65265  arb_id 0x18FEF121
     * bytes[1-2]=0x0050 LE  wheel_speed  raw=20480 → 20480/256 = 80 km/h */
    {0, 0x18FEF121, {0x00, 0x00, 0x50, 0x00, 0x00, 0x00, 0x00, 0x00}},

    /* LFE1  PGN 65266  arb_id 0x18FEF2E6
     * bytes[0-1]=0xF401 LE  fuel_rate  raw=500 → 500*0.05 = 25 L/h */
    {0, 0x18FEF2E6, {0xF4, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},

    /* ETC1  PGN 61442  arb_id 0x18F002E6
     * bytes[1-2]=0x8025 LE  output_shaft_speed  raw=9600 → 9600*0.125 = 1200 rpm
     * bytes[3]=0x00          clutch_slip  raw=0 → 0 %
     * bytes[5-6]=0x8025 LE  input_shaft_speed   raw=9600 → 1200 rpm */
    {0, 0x18F002E6, {0x00, 0x80, 0x25, 0x00, 0x00, 0x80, 0x25, 0x00}},

    /* ETC2  PGN 61445  arb_id 0x18F005E6
     * bytes[0]=0x83  selected_gear  raw=131 → 131-125 = 6
     * bytes[3]=0x83  current_gear   raw=131 → 131-125 = 6 */
    {0, 0x18F005E6, {0x83, 0x00, 0x00, 0x83, 0x00, 0x00, 0x00, 0x00}},

    /* TCO1  PGN 65132  arb_id 0x18FE6CE6
     * bytes[6-7]=0x0050 LE  tachograph_speed  raw=20480 → 80 km/h */
    {0, 0x18FE6CE6, {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x50}},

    /* EBC1  PGN 61441  arb_id 0x18F001E6
     * bytes[1]=0x00  brake_pedal  raw=0 → 0 % */
    {0, 0x18F001E6, {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},

    /* VDC2  PGN 61449  arb_id 0x18F009E6
     * All zeros → raw=0 for all three SPNs.
     * steering_angle = 0*(1/1024) + (-31.374) = -31.374 rad
     * yaw_rate       = 0*(1/8192) + (-3.92)   = -3.920 rad/s
     * lateral_accel  = 0*(1/2048) + (-15.687) = -15.687 m/s²  */
    {0, 0x18F009E6, {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}},

    /* ---- t = 100 ms: triggers grid tick at tick=100 ---- */
    {100, 0x18F004E6, {0x00, 0xAF, 0xB9, 0x80, 0x3E, 0x00, 0x00, 0x00}},

    /* ---- t = 200 ms: triggers grid tick at tick=200 ---- */
    {200, 0x18F004E6, {0x00, 0xAF, 0xB9, 0x80, 0x3E, 0x00, 0x00, 0x00}},
};

#define NUM_FRAMES (sizeof(FRAMES) / sizeof(FRAMES[0]))

int main(void)
{
    GridSampler g;
    grid_sampler_init(&g, 100, 1000, on_row);

    for (size_t i = 0; i < NUM_FRAMES; i++) {
        const Frame *f = &FRAMES[i];
        grid_feed(&g, f->arb_id, f->data, 8, f->now_ms);
    }
    return 0;
}
