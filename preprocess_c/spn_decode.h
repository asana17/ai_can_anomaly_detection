/**
 * spn_decode.h — Extract one J1939 SPN field from a payload as a physical value.
 *
 * Port of preprocess/frames/spn_decode.py.
 */
#ifndef SPN_DECODE_H
#define SPN_DECODE_H

#include <stdint.h>

/**
 * Geometry of one SPN bit-field inside an 8-byte CAN payload.
 *
 * All fields in the SPN spec used by this project are byte-aligned and have
 * byte-multiple lengths, so the fast-path in spn_decode() always applies.
 */
typedef struct {
    uint8_t start_bit; /**< Bit offset of the LSB from the start of the payload. */
    uint8_t length;    /**< Field width in bits (8 or 16 for all tracked SPNs). */
    float   scale;     /**< Multiply raw integer by this to get physical units. */
    float   offset;    /**< Add this after scaling. */
} SpnField;

/**
 * Decode one SPN field to its physical value.
 *
 * Reads `field.length` bits starting at `field.start_bit` (little-endian),
 * applies `raw * scale + offset`, and returns the result.
 *
 * Returns NAN when the J1939 not-available (0xFF top byte) or error (0xFE top
 * byte) marker is set, matching the Python None return.
 *
 * @param data   Payload bytes (up to 8).
 * @param dlc    Number of valid bytes in data.
 * @param field  Bit-field geometry and scaling.
 * @return       Physical value, or NAN if the field is not available.
 */
float spn_decode(const uint8_t *data, uint8_t dlc, SpnField field);

#endif /* SPN_DECODE_H */
