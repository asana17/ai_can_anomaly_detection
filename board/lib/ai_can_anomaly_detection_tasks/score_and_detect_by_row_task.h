#ifndef SCORE_AND_DETECT_BY_ROW_TASK_H
#define SCORE_AND_DETECT_BY_ROW_TASK_H

#include <tk/tkernel.h>
#include "ai_can_anomaly_detection_tasks.h"
#include "copy_alarm_frames_input.h"
#include "report_input.h"
#include "score_and_detect_by_row_input.h"
#include "score_and_detect_by_window_input.h"

/* Score and detect by row gives a verdict on every row. */

/* Where score and detect by row gets rows, sends alarms and passes rows on. */
typedef struct {
	ScoreAndDetectByRowInput *score_and_detect_by_row_input;
	ReportInput *report_input;
	ScoreAndDetectByWindowInput *score_and_detect_by_window_input;
	CopyAlarmFramesInput *copy_alarm_frames_input;
	ID task_id;
} ScoreAndDetectByRowTask;

/*
 * Create score and detect by row. Rows come from its input, alarms go to report_input,
 * each row goes on to score_and_detect_by_window_input, and the frame ring's positions
 * behind each alarm start go to copy_alarm_frames_input.
 */
IMPORT ER score_and_detect_by_row_task_create(ScoreAndDetectByRowTask *task,
	PRI priority, ScoreAndDetectByRowInput *score_and_detect_by_row_input,
	ReportInput *report_input,
	ScoreAndDetectByWindowInput *score_and_detect_by_window_input,
	CopyAlarmFramesInput *copy_alarm_frames_input);

/* Start score and detect by row. */
IMPORT ER score_and_detect_by_row_task_start(ScoreAndDetectByRowTask *task);

#endif
