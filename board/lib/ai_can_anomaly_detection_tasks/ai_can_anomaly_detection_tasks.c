#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "copy_alarm_frames_input.h"
#include "copy_alarm_frames_task.h"
#include "preprocess_task.h"
#include "report_input.h"
#include "score_and_detect_by_row_input.h"
#include "score_and_detect_by_row_task.h"
#include "score_and_detect_by_window_input.h"
#include "score_and_detect_by_window_task.h"
#include "ai_can_anomaly_detection_tasks.h"

LOCAL ScoreAndDetectByRowInput score_and_detect_by_row_input;
LOCAL ScoreAndDetectByWindowInput score_and_detect_by_window_input;
LOCAL CopyAlarmFramesInput copy_alarm_frames_input;
LOCAL PreprocessTask preprocess_task;
LOCAL ScoreAndDetectByRowTask score_and_detect_by_row_task;
LOCAL ScoreAndDetectByWindowTask score_and_detect_by_window_task;
LOCAL CopyAlarmFramesTask copy_alarm_frames_task;


EXPORT ER ai_can_anomaly_detection_tasks_create(Slots *slots, FrameRing *frame_ring,
	ReportInput *report_input, StoreAlarmFramesInput *store_alarm_frames_input)
{
	ER error;

	error = model_init();
	if (error != MODEL_OK) {
		tm_printf((UB*)"model init error %d\n", error);
		return error;
	}
	error = score_and_detect_by_row_input_create(&score_and_detect_by_row_input);
	if (error < E_OK) {
		return error;
	}
	error = score_and_detect_by_window_input_create(&score_and_detect_by_window_input);
	if (error < E_OK) {
		return error;
	}
	error = copy_alarm_frames_input_create(&copy_alarm_frames_input);
	if (error < E_OK) {
		return error;
	}
	preprocess_task.slots = slots;
	preprocess_task.frame_ring = frame_ring;
	/* the windowed model is best effort, so it sits below the alarm outputs */
	error = score_and_detect_by_window_task_create(&score_and_detect_by_window_task, 11,
		&score_and_detect_by_window_input);
	if (error < E_OK) {
		return error;
	}
	/*
	 * above the windowed model, since the ring overwrites the frames it has not copied,
	 * and below the alarm outputs
	 */
	error = copy_alarm_frames_task_create(&copy_alarm_frames_task, 10,
		&copy_alarm_frames_input, frame_ring, store_alarm_frames_input);
	if (error < E_OK) {
		return error;
	}
	error = score_and_detect_by_row_task_create(&score_and_detect_by_row_task, 8,
		&score_and_detect_by_row_input, report_input, &score_and_detect_by_window_input,
		&copy_alarm_frames_input);
	if (error < E_OK) {
		return error;
	}
	return preprocess_task_create(&preprocess_task, 6, &score_and_detect_by_row_input);
}

EXPORT ER ai_can_anomaly_detection_tasks_start(void)
{
	ER error;

	/* each task waits on its input before the one that writes to it runs */
	error = score_and_detect_by_window_task_start(&score_and_detect_by_window_task);
	if (error < E_OK) {
		return error;
	}
	error = copy_alarm_frames_task_start(&copy_alarm_frames_task);
	if (error < E_OK) {
		return error;
	}
	error = score_and_detect_by_row_task_start(&score_and_detect_by_row_task);
	if (error < E_OK) {
		return error;
	}
	return preprocess_task_start(&preprocess_task);
}
