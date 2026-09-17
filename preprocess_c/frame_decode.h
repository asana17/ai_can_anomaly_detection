/**
 * frame_decode.h — Decode all known SPNs of one CAN frame.
 *
 * Port of preprocess/frames/frame_decode.py.
 *
 * This is intentionally a header-only inline so the compiler can fold it into
 * grid_feed() with zero call overhead.
 *
 * Usage:
 *   float incoming[NUM_SIGNALS];
 *   for (int i = 0; i < NUM_SIGNALS; i++) incoming[i] = NAN;
 *   frame_decode(pgn, data, dlc, incoming);
 *   // incoming[i] is NAN for signals not in this PGN, or not available.
 */
#ifndef FRAME_DECODE_H
#define FRAME_DECODE_H

#include "spn_spec.h"
#include <math.h>    /* NAN */

/**
 * Decode all SPNs of `pgn` into `values[signal_index]`.
 *
 * Only the slots belonging to `pgn` are written; the rest are left untouched
 * (caller should initialise to NAN before calling).  NA fields (spn_decode
 * returns NAN) are also left untouched so the hold-last state is not
 * overwritten with a missing reading.
 *
 * @param pgn     PGN extracted from the CAN ID.
 * @param data    Payload bytes.
 * @param dlc     Number of valid bytes in data.
 * @param values  Output array of NUM_SIGNALS floats.
 */
static inline void frame_decode(uint32_t pgn, const uint8_t *data, uint8_t dlc,
                                 float values[NUM_SIGNALS])
{
    const PgnEntry *entry = spn_spec_lookup(pgn);
    if (!entry) return;

    for (uint8_t i = 0u; i < entry->count; i++) {
        float v = spn_decode(data, dlc, entry->defs[i].field);
        if (!isnan(v))
            values[entry->defs[i].signal_index] = v;
    }
}

#endif /* FRAME_DECODE_H */
