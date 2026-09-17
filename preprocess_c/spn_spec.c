/**
 * spn_spec.c — Static SPN decode table.
 *
 * Port of preprocess/frames/spn_spec.py.
 *
 * All values are taken directly from the Python SPEC dict, preserving the
 * same PGN insertion order so that signal_index matches the Python SIGNALS
 * list at every position.
 *
 * SpnField initialiser: {start_bit, length, scale, offset}
 * SpnDef  initialiser: {spn, signal_index, field, minimum, maximum}
 */
#include "spn_spec.h"

#include <stddef.h>   /* NULL */

/* ---------------------------------------------------------------------------
 * Per-PGN SPN arrays (static, not exposed outside this TU)
 * --------------------------------------------------------------------------- */

/* EEC1 — PGN 61444 */
static const SpnDef EEC1_DEFS[] = {
    /* SPN 190  engine_speed          idx=0  bytes 3-4  scale 0.125  offset 0 */
    { 190, 0, {24, 16, 0.125f,    0.0f},    0.0f,    8031.875f },
    /* SPN 512  driver_demand_torque  idx=1  byte 1    scale 1.0  offset -125 */
    { 512, 1, { 8,  8, 1.0f,   -125.0f}, -125.0f,     125.0f  },
    /* SPN 513  actual_engine_torque  idx=2  byte 2    scale 1.0  offset -125 */
    { 513, 2, {16,  8, 1.0f,   -125.0f}, -125.0f,     125.0f  },
};

/* EEC2 — PGN 61443 */
static const SpnDef EEC2_DEFS[] = {
    /* SPN 91   accel_pedal           idx=3  byte 1    scale 0.4  offset 0 */
    {  91, 3, { 8,  8, 0.4f,     0.0f},    0.0f,     100.0f  },
    /* SPN 92   engine_load           idx=4  byte 2    scale 1.0  offset 0 */
    {  92, 4, {16,  8, 1.0f,     0.0f},    0.0f,     250.0f  },
};

/* CCVS1 — PGN 65265 */
static const SpnDef CCVS1_DEFS[] = {
    /* SPN 84   wheel_speed           idx=5  bytes 1-2  scale 1/256 ≈ 0.00390625  offset 0 */
    {  84, 5, { 8, 16, 0.00390625f, 0.0f},  0.0f,     250.996f },
};

/* LFE1 — PGN 65266 */
static const SpnDef LFE1_DEFS[] = {
    /* SPN 183  fuel_rate             idx=6  bytes 0-1  scale 0.05  offset 0 */
    { 183, 6, { 0, 16, 0.05f,    0.0f},    0.0f,    3212.75f },
};

/* ETC1 — PGN 61442 */
static const SpnDef ETC1_DEFS[] = {
    /* SPN 191  output_shaft_speed    idx=7  bytes 1-2  scale 0.125  offset 0 */
    { 191, 7, { 8, 16, 0.125f,   0.0f},    0.0f,    8031.875f },
    /* SPN 522  clutch_slip           idx=8  byte 3    scale 0.4  offset 0 */
    { 522, 8, {24,  8, 0.4f,     0.0f},    0.0f,     100.0f  },
    /* SPN 161  input_shaft_speed     idx=9  bytes 5-6  scale 0.125  offset 0 */
    { 161, 9, {40, 16, 0.125f,   0.0f},    0.0f,    8031.875f },
};

/* ETC2 — PGN 61445 */
static const SpnDef ETC2_DEFS[] = {
    /* SPN 524  selected_gear         idx=10  byte 0  scale 1.0  offset -125 */
    { 524, 10, { 0,  8, 1.0f,  -125.0f}, -125.0f,    125.0f  },
    /* SPN 523  current_gear          idx=11  byte 3  scale 1.0  offset -125 */
    { 523, 11, {24,  8, 1.0f,  -125.0f}, -125.0f,    125.0f  },
};

/* TCO1 — PGN 65132 */
static const SpnDef TCO1_DEFS[] = {
    /*
     * SPN 1624  tachograph_speed     idx=12  bytes 6-7
     * scale = 1/256 ≈ 0.00390625  offset 0
     * (Python: 1/256 stored as float32 = 0.00390625f exactly)
     */
    { 1624, 12, {48, 16, 0.00390625f, 0.0f},  0.0f,  250.996f },
};

/* EBC1 — PGN 61441 */
static const SpnDef EBC1_DEFS[] = {
    /* SPN 521  brake_pedal           idx=13  byte 1  scale 0.4  offset 0 */
    { 521, 13, { 8,  8, 0.4f,    0.0f},    0.0f,    100.0f  },
};

/* VDC2 — PGN 61449 */
static const SpnDef VDC2_DEFS[] = {
    /*
     * SPN 1807  steering_angle       idx=14  bytes 0-1
     * scale = 1/1024  offset = -31.374
     * 1/1024 = 0.0009765625f exactly in float32
     */
    { 1807, 14, { 0, 16, 0.0009765625f, -31.374f}, -31.374f, 31.374f },
    /*
     * SPN 1811  yaw_rate             idx=15  bytes 3-4
     * scale = 1/8192 ≈ 0.0001220703125f  offset = -3.92
     */
    { 1811, 15, {24, 16, 0.0001220703125f, -3.92f}, -3.92f,  3.92f  },
    /*
     * SPN 1809  lateral_accel        idx=16  bytes 5-6
     * scale = 1/2048 ≈ 0.00048828125f  offset = -15.687
     */
    { 1809, 16, {40, 16, 0.00048828125f, -15.687f}, -15.687f, 15.687f },
};

/* ---------------------------------------------------------------------------
 * Public tables
 * --------------------------------------------------------------------------- */

const char * const SIGNAL_NAMES[NUM_SIGNALS] = {
    "engine_speed",         /*  0 */
    "driver_demand_torque", /*  1 */
    "actual_engine_torque", /*  2 */
    "accel_pedal",          /*  3 */
    "engine_load",          /*  4 */
    "wheel_speed",          /*  5 */
    "fuel_rate",            /*  6 */
    "output_shaft_speed",   /*  7 */
    "clutch_slip",          /*  8 */
    "input_shaft_speed",    /*  9 */
    "selected_gear",        /* 10 */
    "current_gear",         /* 11 */
    "tachograph_speed",     /* 12 */
    "brake_pedal",          /* 13 */
    "steering_angle",       /* 14 */
    "yaw_rate",             /* 15 */
    "lateral_accel",        /* 16 */
};

/* Same insertion order as the Python SPEC dict. */
const PgnEntry PGN_TABLE[NUM_PGNS] = {
    { 61444, EEC1_DEFS,  3 },   /* EEC1  */
    { 61443, EEC2_DEFS,  2 },   /* EEC2  */
    { 65265, CCVS1_DEFS, 1 },   /* CCVS1 */
    { 65266, LFE1_DEFS,  1 },   /* LFE1  */
    { 61442, ETC1_DEFS,  3 },   /* ETC1  */
    { 61445, ETC2_DEFS,  2 },   /* ETC2  */
    { 65132, TCO1_DEFS,  1 },   /* TCO1  */
    { 61441, EBC1_DEFS,  1 },   /* EBC1  */
    { 61449, VDC2_DEFS,  3 },   /* VDC2  */
};

const PgnEntry *spn_spec_lookup(uint32_t pgn)
{
    for (uint8_t i = 0u; i < NUM_PGNS; i++) {
        if (PGN_TABLE[i].pgn == pgn)
            return &PGN_TABLE[i];
    }
    return NULL;
}
