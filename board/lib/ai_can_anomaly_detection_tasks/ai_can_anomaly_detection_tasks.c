#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "preprocess_task.h"
#include "report_input.h"
#include "report_task.h"
#include "score_and_detect_by_row_input.h"
#include "score_and_detect_by_row_task.h"
#include "ai_can_anomaly_detection_tasks.h"

LOCAL ScoreAndDetectByRowInput score_and_detect_by_row_input;
LOCAL ReportInput report_input;
LOCAL PreprocessTask preprocess_task;
LOCAL ScoreAndDetectByRowTask score_and_detect_by_row_task;
LOCAL ReportTask report_task;


EXPORT ER ai_can_anomaly_detection_tasks_create(Slots *slots)
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
	error = report_input_create(&report_input);
	if (error < E_OK) {
		return error;
	}
	preprocess_task.slots = slots;
	report_task.model_id = score_and_detect_by_row_model_id;
	/* report sits below the tasks that raise the alarm */
	error = report_task_create(&report_task, 10, &report_input);
	if (error < E_OK) {
		return error;
	}
	error = score_and_detect_by_row_task_create(&score_and_detect_by_row_task, 8,
		&score_and_detect_by_row_input, &report_input);
	if (error < E_OK) {
		return error;
	}
	return preprocess_task_create(&preprocess_task, 6, &score_and_detect_by_row_input);
}

EXPORT ER ai_can_anomaly_detection_tasks_start(void)
{
	ER error;

	/* each task waits on its input before the one that writes to it runs */
	error = report_task_start(&report_task);
	if (error < E_OK) {
		return error;
	}
	error = score_and_detect_by_row_task_start(&score_and_detect_by_row_task);
	if (error < E_OK) {
		return error;
	}
	return preprocess_task_start(&preprocess_task);
}
