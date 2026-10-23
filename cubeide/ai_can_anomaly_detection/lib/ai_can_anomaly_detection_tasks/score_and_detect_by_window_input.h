#ifndef SCORE_AND_DETECT_BY_WINDOW_INPUT_H
#define SCORE_AND_DETECT_BY_WINDOW_INPUT_H

#include <stdbool.h>
#include <tk/tkernel.h>
#include "row_ring.h"

/*
 * The rows score and detect by row passes to score and detect by window, each with its
 * flag, in a RowRing under a lock. Reading takes every row out. A new row on a full ring
 * goes over the oldest, which was never read.
 */
typedef struct {
	ID mutex;            /* locks row_ring */
	ID wake_reader_flag; /* event flag that wakes the reader */
	RowRing row_ring;    /* the rows not read yet */
} ScoreAndDetectByWindowInput;

/**
 * @brief Make the ring, with no row in it.
 *
 * @param[out] score_and_detect_by_window_input The ring.
 * @return E_OK, or the error T-Kernel gave while making its mutex or event flag.
 */
IMPORT ER score_and_detect_by_window_input_create(ScoreAndDetectByWindowInput *score_and_detect_by_window_input);

/**
 * @brief Add a row over the oldest, and wake the reader.
 *
 * @param[in,out] score_and_detect_by_window_input The ring.
 * @param[in] entry The row.
 */
IMPORT void score_and_detect_by_window_input_write(ScoreAndDetectByWindowInput *score_and_detect_by_window_input,
	CONST RowRingEntry *entry);

/**
 * @brief Check whether a row is waiting in the ring.
 *
 * @param[in,out] score_and_detect_by_window_input The ring.
 * @retval true A row was written and not taken yet.
 * @retval false None is waiting.
 */
IMPORT bool score_and_detect_by_window_input_has_rows(ScoreAndDetectByWindowInput *score_and_detect_by_window_input);

/**
 * @brief Wait for a write, then take every row out of the ring.
 *
 * @param[in,out] score_and_detect_by_window_input The ring.
 * @param[out] dest_row_ring Where the rows are copied, oldest first.
 */
IMPORT void score_and_detect_by_window_input_read(ScoreAndDetectByWindowInput *score_and_detect_by_window_input,
	RowRing *dest_row_ring);

#endif
