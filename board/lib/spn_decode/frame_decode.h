#ifndef BOARD_FRAME_DECODE_H
#define BOARD_FRAME_DECODE_H

#include <stddef.h>
#include <stdint.h>

#include "spn_decode.h"
#include "spn_spec.h"

typedef struct {
	size_t signal; /* index in SPN_SPEC, the order of SIGNALS */
	float value;
} FrameDecodeValue;

/**
 * @brief Decode every known SPN of one frame, skipping the unavailable ones.
 *
 * The C port of decode_frame in preprocess/frames/frame_decode.py.
 *
 * @param[in] pgn The frame's PGN.
 * @param[in] data The payload.
 * @param[in] size Bytes in @p data.
 * @param[out] out The decoded values, in the order of SIGNALS.
 * @return The number of values written to @p out, 0 for a PGN not in SPN_SPEC.
 * @pre @p out has room for SPN_SPEC_SIGNALS elements.
 */
static inline size_t frame_decode(uint32_t pgn, const uint8_t data[], size_t size,
				  FrameDecodeValue out[])
{
	size_t count = 0;
	size_t i;

	for(i = 0; i < SPN_SPEC_SIGNALS; i++) {
		if(SPN_SPEC[i].pgn == pgn && spn_decode(data, size, &SPN_SPEC[i].field,
							&out[count].value)) {
			out[count].signal = i;
			count++;
		}
	}
	return count;
}

#endif
