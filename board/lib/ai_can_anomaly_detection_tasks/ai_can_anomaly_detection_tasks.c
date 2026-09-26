#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "mbf.h"
#include "preprocess_task.h"
#include "report_task.h"
#include "scoring_and_detect_task.h"
#include "ai_can_anomaly_detection_tasks.h"

#define ROW_DEPTH 4
#define REPORT_DEPTH 8

LOCAL PreprocessTask preprocess_task;
LOCAL ScoringAndDetectTask scoring_and_detect_task;
LOCAL ReportTask report_task;

/* The queue from preprocess to scoring and detect, a Row each. */
LOCAL T_CMBF row_cmbf = {
	.mbfatr = TA_TFIFO,
	.bufsz = ROW_DEPTH * MBF_MESSAGE_STORAGE_SIZE(sizeof(Row)),
	.maxmsz = sizeof(Row),
};
/* The queue from scoring and detect to report, a Report each. */
LOCAL T_CMBF report_cmbf = {
	.mbfatr = TA_TFIFO,
	.bufsz = REPORT_DEPTH * MBF_MESSAGE_STORAGE_SIZE(sizeof(Report)),
	.maxmsz = sizeof(Report),
};

EXPORT ER ai_can_anomaly_detection_tasks_create(Slots *slots)
{
	ID row_mbf, report_mbf;
	ER error;

	error = model_init();
	if(error != MODEL_OK) {
		tm_printf((UB*)"model init error %d\n", error);
		return error;
	}
	row_mbf = tk_cre_mbf(&row_cmbf);
	if(row_mbf < E_OK) {
		return row_mbf;
	}
	report_mbf = tk_cre_mbf(&report_cmbf);
	if(report_mbf < E_OK) {
		return report_mbf;
	}
	preprocess_task.slots = slots;
	report_task.model_id = scoring_and_detect_model_id;
	/* report sits below the tasks that raise the alarm */
	error = report_task_create(&report_task, 10, report_mbf);
	if(error < E_OK) {
		return error;
	}
	error = scoring_and_detect_task_create(&scoring_and_detect_task, 8, row_mbf,
		report_mbf);
	if(error < E_OK) {
		return error;
	}
	return preprocess_task_create(&preprocess_task, 6, row_mbf);
}

EXPORT ER ai_can_anomaly_detection_tasks_start(void)
{
	ER error;

	/* each task waits on its queue before the one that sends to it runs */
	error = report_task_start(&report_task);
	if(error < E_OK) {
		return error;
	}
	error = scoring_and_detect_task_start(&scoring_and_detect_task);
	if(error < E_OK) {
		return error;
	}
	return preprocess_task_start(&preprocess_task);
}
