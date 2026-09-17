/**
 * spn_spec.h — Static SPN decode table: which SPNs each PGN carries.
 *
 * Port of preprocess/frames/spn_spec.py.
 *
 * The 17 tracked signals and their indices are fixed at compile time.
 * The signal_index field in SpnDef gives the column position in every
 * row array, preserving the same order as the Python SIGNALS list:
 *
 *  0  engine_speed          (EEC1 / PGN 61444)
 *  1  driver_demand_torque  (EEC1)
 *  2  actual_engine_torque  (EEC1)
 *  3  accel_pedal           (EEC2 / PGN 61443)
 *  4  engine_load           (EEC2)
 *  5  wheel_speed           (CCVS1 / PGN 65265)
 *  6  fuel_rate             (LFE1 / PGN 65266)
 *  7  output_shaft_speed    (ETC1 / PGN 61442)
 *  8  clutch_slip           (ETC1)
 *  9  input_shaft_speed     (ETC1)
 * 10  selected_gear         (ETC2 / PGN 61445)
 * 11  current_gear          (ETC2)
 * 12  tachograph_speed      (TCO1 / PGN 65132)
 * 13  brake_pedal           (EBC1 / PGN 61441)
 * 14  steering_angle        (VDC2 / PGN 61449)
 * 15  yaw_rate              (VDC2)
 * 16  lateral_accel         (VDC2)
 */
#ifndef SPN_SPEC_H
#define SPN_SPEC_H

#include "spn_decode.h"

#define NUM_SIGNALS 17u  /**< Total number of decoded signals in one row. */
#define NUM_PGNS     9u  /**< Number of PGNs that carry tracked signals. */

/** One SPN: its number, row position, decode geometry, and J1939 range. */
typedef struct {
    uint16_t spn;           /**< SPN number (for reference). */
    uint8_t  signal_index;  /**< Column in the 17-element row (see header). */
    SpnField field;         /**< Bit-field geometry and scaling. */
    float    minimum;       /**< J1939 defined lower bound (used by range_check). */
    float    maximum;       /**< J1939 defined upper bound. */
} SpnDef;

/** All SPNs belonging to one PGN. */
typedef struct {
    uint32_t      pgn;
    const SpnDef *defs;
    uint8_t       count;
} PgnEntry;

/**
 * Human-readable signal names, indexed by signal_index.
 * Matches the Python SIGNALS list exactly.
 */
extern const char * const SIGNAL_NAMES[NUM_SIGNALS];

/** The 9-entry PGN lookup table, in the same insertion order as the Python dict. */
extern const PgnEntry PGN_TABLE[NUM_PGNS];

/**
 * Look up a PGN in PGN_TABLE.
 *
 * @param pgn  PGN to search for.
 * @return     Pointer to the matching PgnEntry, or NULL if not tracked.
 */
const PgnEntry *spn_spec_lookup(uint32_t pgn);

#endif /* SPN_SPEC_H */
