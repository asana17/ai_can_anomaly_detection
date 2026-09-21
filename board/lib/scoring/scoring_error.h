#ifndef BOARD_SCORING_ERROR_H
#define BOARD_SCORING_ERROR_H

#include <stddef.h>

/**
 * @brief Take the autoencoder's score for a row, its mean squared reconstruction error.
 *
 * The C port of the error the scorers in models/ take, `((got - fed) ** 2).mean(axis=1)`
 * in models/onnx_files.py. It sums in signal order, where numpy may sum in another.
 *
 * @param[in] scaled The scaled row the model was fed.
 * @param[in] reconstructed The model's reconstruction of it.
 * @param[in] signals Number of elements in both arrays.
 * @return The mean of the squared differences.
 */
static inline float scoring_error(const float scaled[], const float reconstructed[],
	size_t signals)
{
	float total = 0.0f;
	size_t i;

	for(i = 0; i < signals; i++) {
		const float difference = scaled[i] - reconstructed[i];
		total += difference * difference;
	}
	return total / signals;
}

#endif
