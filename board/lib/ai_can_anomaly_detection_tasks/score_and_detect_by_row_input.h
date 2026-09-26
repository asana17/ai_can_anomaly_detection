#ifndef SCORE_AND_DETECT_BY_ROW_INPUT_H
#define SCORE_AND_DETECT_BY_ROW_INPUT_H

#include <tk/tkernel.h>
#include "model.h"

/* A row preprocess built. */
typedef struct {
	UW no; /* the tick it was built on */
	float physical[SIGNAL_COUNT];
} Row;

/*
 * The rows preprocess passes to score and detect by row, in a message buffer. When it is
 * full, the oldest row is dropped to make room.
 */
typedef struct {
	ID mbf;
} ScoreAndDetectByRowInput;

/**
 * @brief Make the input, with no row in it.
 *
 * @param[out] score_and_detect_by_row_input The input.
 * @return E_OK, or the error T-Kernel gave while making its message buffer.
 */
IMPORT ER score_and_detect_by_row_input_create(
	ScoreAndDetectByRowInput *score_and_detect_by_row_input);

/**
 * @brief Add a row, dropping the oldest when the input is full.
 *
 * @param[in,out] score_and_detect_by_row_input The input.
 * @param[in] row The row.
 * @return E_OK, or the error T-Kernel gave.
 */
IMPORT ER score_and_detect_by_row_input_write(
	ScoreAndDetectByRowInput *score_and_detect_by_row_input, CONST Row *row);

/**
 * @brief Wait for a row and take it out.
 *
 * @param[in,out] score_and_detect_by_row_input The input.
 * @param[out] row The row.
 * @return E_OK, or the error T-Kernel gave.
 */
IMPORT ER score_and_detect_by_row_input_read(
	ScoreAndDetectByRowInput *score_and_detect_by_row_input, Row *row);

#endif
