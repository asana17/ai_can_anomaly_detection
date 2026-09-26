#include <string.h>
#include <tk/tkernel.h>
#include "detect_instant.h"
#include "model.h"
#include "model_config.h"
#include "scoring.h"
#include "score_and_detect_by_row_task.h"
#include "ai_can_anomaly_detection_tasks.h"
#include "threshold.h"

EXPORT CONST char *CONST score_and_detect_by_row_model_id = ACTIVE_MODEL_ID;

/* Score each row and report where alarms start and end. */
LOCAL void score_and_detect_by_row_task(INT stacd, void *exinf)
{
	ScoreAndDetectByRowTask *task = exinf;
	DetectInstant state;
	ScoringRow scored;
	Row row;
	Report report = {0};
	INT ringing = 0, alarmed;

	detect_instant_init(&state, THRESHOLD_SCORE, ALARM_K);
	while (tk_rcv_mbf(task->row_mbf, &row, TMO_FEVR) == sizeof(row)) {
		report.error = scoring_row(row.physical, active_model_mean, active_model_std,
			MIN_SPEED, &scored);
		if (report.error != MODEL_OK) {
			report.no = row.no;
			tk_snd_mbf(task->report_mbf, &report, sizeof(report), TMO_FEVR);
			break;
		}
		detect_instant_add_row(&state, row.no, scored.score, scored.rule_hit);
		alarmed = detect_instant_alarmed(&state);
		if (alarmed != ringing) {
			report.no = row.no;
			memcpy(&report.score_bits, &scored.score, sizeof(scored.score));
			report.rule = scored.rule_hit;
			report.alarm = alarmed;
			tk_snd_mbf(task->report_mbf, &report, sizeof(report), TMO_FEVR);
			ringing = alarmed;
		}
	}
	tk_ext_tsk();
}

EXPORT ER score_and_detect_by_row_task_create(ScoreAndDetectByRowTask *task,
	PRI priority, ID row_mbf, ID report_mbf)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = score_and_detect_by_row_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};

	task->row_mbf = row_mbf;
	task->report_mbf = report_mbf;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER score_and_detect_by_row_task_start(ScoreAndDetectByRowTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
