#ifndef BOARD_SPN_DECODE_H
#define BOARD_SPN_DECODE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
	uint8_t start_bit;
	uint8_t length;
	float scale;
	float offset;
} SpnField;

/**
 * @brief Read bits of a payload as an unsigned little-endian integer.
 *
 * The C port of extract_le in preprocess/frames/spn_decode.py. Bits past the payload
 * read as 0.
 *
 * @param[in] data The payload.
 * @param[in] size Bytes in @p data.
 * @param[in] start_bit The first bit, counted from bit 0 of byte 0.
 * @param[in] length Bits to read, at most 32.
 * @return The bits read.
 */
static inline uint32_t spn_decode_extract_le(const uint8_t data[], size_t size,
					     unsigned start_bit, unsigned length)
{
	uint32_t value = 0;
	unsigned i;

	for(i = 0; i < length; i++) {
		unsigned bit = start_bit + i;

		if((bit >> 3) < size && (data[bit >> 3] >> (bit & 7u)) & 1u) {
			value |= (uint32_t)1 << i;
		}
	}
	return value;
}

/**
 * @brief Decode one field of a payload to its physical value.
 *
 * The C port of decode in preprocess/frames/spn_decode.py. The product is rounded before
 * the offset is added, as on the PC, so the build needs -ffp-contract=off.
 *
 * @param[in] data The payload.
 * @param[in] size Bytes in @p data.
 * @param[in] field Where the field sits and how it scales.
 * @param[out] value The physical value, written only when the field is available.
 * @retval true The field holds a value.
 * @retval false J1939 reserves the value, 0xFE for an error or 0xFF for not available.
 */
static inline bool spn_decode(const uint8_t data[], size_t size, const SpnField *field,
			      float *value)
{
	uint32_t raw = spn_decode_extract_le(data, size, field->start_bit, field->length);
	unsigned shift = 0;

	if(field->length > 8) {
		shift = field->length - 8u;
	}
	if((raw >> shift) >= 0xFEu) {
		return false;
	}
	*value = (float)raw * field->scale + field->offset;
	return true;
}

#endif
