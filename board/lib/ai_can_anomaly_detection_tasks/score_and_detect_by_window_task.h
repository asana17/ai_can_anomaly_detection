#ifndef SCORE_AND_DETECT_BY_WINDOW_TASK_H
#define SCORE_AND_DETECT_BY_WINDOW_TASK_H

#include <tk/tkernel.h>
#include "ai_can_anomaly_detection_tasks.h"
#include "copy_alarm_frames_input.h"
#include "report_input.h"
#include "window_backlog_input.h"
#include "row_ring.h"
#include "row_ring_as_window.h"
#include "score_and_detect_by_window_input.h"
#include "window_model_run.h"

/* Score and detect by window builds windows from the rows and scores them when it can. */

/* Where score and detect by window gets rows, and the rows it keeps. */
typedef struct {
	ScoreAndDetectByWindowInput *score_and_detect_by_window_input;
	ReportInput *window_report_input;     /* where the window alarm goes */
	WindowBacklogInput *window_backlog_input; /* where the backlogs go */
	CopyAlarmFramesInput *copy_window_alarm_frames_input; /* window alarm starts */
	ID task_id;
	RowRing row_ring;                     /* the rows of one read */
	RowRingAsWindow row_ring_as_window;   /* the rows it builds windows from */
	float scaled[WINDOW_MODEL_VALUES];        /* the window as the model takes it */
	float reconstructed[WINDOW_MODEL_VALUES]; /* the model's output for it */
} ScoreAndDetectByWindowTask;

/*
 * Create score and detect by window, reading score_and_detect_by_window_input. The window
 * alarm goes to window_report_input. A row it finishes while the next is waiting, or
 * the first after rows it lost, goes to window_backlog_input. The frame ring's positions
 * behind each window alarm start go to copy_window_alarm_frames_input.
 */
IMPORT ER score_and_detect_by_window_task_create(ScoreAndDetectByWindowTask *task,
	PRI priority, ScoreAndDetectByWindowInput *score_and_detect_by_window_input,
	ReportInput *window_report_input, WindowBacklogInput *window_backlog_input,
	CopyAlarmFramesInput *copy_window_alarm_frames_input);

/* Start score and detect by window. */
IMPORT ER score_and_detect_by_window_task_start(ScoreAndDetectByWindowTask *task);

#endif
