#ifndef BOARD_SCALE_H
#define BOARD_SCALE_H

#include <stddef.h>

/**
 * @brief Z-score one row.
 *
 * Computes `scaled[i] = (physical[i] - mean[i]) / std[i]`. `physical` and
 * `scaled` may point to the same array.
 *
 * @param[in] physical Physical signal values.
 * @param[in] mean Training-set mean for each signal.
 * @param[in] std Positive training-set standard deviation for each signal.
 * @param[out] scaled Scaled signal values.
 * @param[in] signals Number of elements in every array.
 * @pre All four arrays contain at least @p signals elements.
 * @pre Every element of @p std is greater than zero.
 */
void scale_row(const float physical[], const float mean[], const float std[],
	float scaled[], size_t signals);

#endif
