/**
 * spn_decode.c — Extract one J1939 SPN field from a payload as a physical value.
 *
 * Port of preprocess/frames/spn_decode.py.
 *
 * All 17 SPNs tracked by this project are byte-aligned and have byte-multiple
 * lengths (8 or 16 bits), so extract_le always takes the fast path.  The
 * general bit-loop is kept for completeness and future use.
 *
 * J1939 error / not-available convention (section 5.3 of SAE J1939-71):
 *   For an n-byte field the top byte indicates validity.
 *   0xFE  → parameter-specific indicator (error / out of range)
 *   0xFF  → not available
 *   Both are treated as missing and returned as NAN.
 */
#include "spn_decode.h"

#include <math.h>    /* NAN, isnan */

/* ---------------------------------------------------------------------------
 * Internal helpers
 * --------------------------------------------------------------------------- */

/**
 * Read `length` bits at `start_bit` as an unsigned little-endian integer.
 *
 * Fast path (all tracked SPNs): when both start_bit and length are multiples
 * of 8, reads whole bytes directly — identical to Python's
 * int.from_bytes(data[start:start+n], "little").
 *
 * General path: shifts and OR-s individual bits, LSB first.
 */
static uint32_t extract_le(const uint8_t *data, uint8_t dlc,
                            uint8_t start_bit, uint8_t length)
{
    /* Fast path — byte-aligned, byte-multiple field. */
    if ((start_bit & 7u) == 0u && (length & 7u) == 0u) {
        uint8_t  start = (uint8_t)(start_bit >> 3);
        uint8_t  bytes = (uint8_t)(length    >> 3);
        uint32_t val   = 0u;
        for (uint8_t i = 0u; i < bytes; i++) {
            if ((uint8_t)(start + i) < dlc)
                val |= (uint32_t)data[start + i] << (8u * i);
        }
        return val;
    }

    /* General path — arbitrary bit position. */
    uint32_t val = 0u;
    for (uint8_t i = 0u; i < length; i++) {
        uint8_t bit      = (uint8_t)(start_bit + i);
        uint8_t byte_idx = (uint8_t)(bit >> 3);
        if (byte_idx < dlc && ((data[byte_idx] >> (bit & 7u)) & 1u))
            val |= (uint32_t)1u << i;
    }
    return val;
}

/* ---------------------------------------------------------------------------
 * Public API
 * --------------------------------------------------------------------------- */

float spn_decode(const uint8_t *data, uint8_t dlc, SpnField field)
{
    uint32_t raw = extract_le(data, dlc, field.start_bit, field.length);

    /*
     * Check the J1939 not-available / error markers.
     *
     * Python: top_byte = raw >> max(field.length - 8, 0)
     *   length == 8  → shift 0 → top_byte = raw itself
     *   length == 16 → shift 8 → top_byte = high byte
     */
    uint8_t  shift    = (field.length > 8u) ? (uint8_t)(field.length - 8u) : 0u;
    uint32_t top_byte = raw >> shift;
    if (top_byte >= 0xFEu)
        return NAN;

    return (float)raw * field.scale + field.offset;
}
