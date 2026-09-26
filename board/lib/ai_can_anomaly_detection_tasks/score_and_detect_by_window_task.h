#ifndef SCORE_AND_DETECT_BY_WINDOW_TASK_H
#define SCORE_AND_DETECT_BY_WINDOW_TASK_H

#include <tk/tkernel.h>
#include "ai_can_anomaly_detection_tasks.h"
#include "row_ring.h"
#include "row_ring_as_window.h"
#include "score_and_detect_by_window_input.h"

/* Score and detect by window builds windows from the rows and scores them when it can. */

/* Where score and detect by window gets rows, and the rows it keeps. */
typedef struct {
	ScoreAndDetectByWindowInput *score_and_detect_by_window_input;
	ID task_id;
	RowRing row_ring;                     /* the rows of one read */
	RowRingAsWindow row_ring_as_window;   /* the rows it builds windows from */
} ScoreAndDetectByWindowTask;

/* Create score and detect by window, reading score_and_detect_by_window_input. */
IMPORT ER score_and_detect_by_window_task_create(ScoreAndDetectByWindowTask *task,
	PRI priority, ScoreAndDetectByWindowInput *score_and_detect_by_window_input);

/* Start score and detect by window. */
IMPORT ER score_and_detect_by_window_task_start(ScoreAndDetectByWindowTask *task);

#endif
