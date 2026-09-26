#include <string.h>
#include <tk/tkernel.h>
#include "detect_instant.h"
#include "model.h"
#include "model_config.h"
#include "recent_rows.h"
#include "scoring.h"
#include "score_and_detect_by_row_task.h"
#include "ai_can_anomaly_detection_tasks.h"
#include "threshold.h"

/* Hand report the row an alarm starts or ends on. */
LOCAL void report_alarm_change(ReportInput *report_input, UW no, INT alarm)
{
	Report report = {0};

	report.no = no;
	report.alarm = alarm;
	report_input_write(report_input, &report);
}

/* Hand score and detect by window the row, its flag and its count since the last gap. */
LOCAL void pass_row_to_window(ScoreAndDetectByWindowInput *window_input, CONST Row *row,
	bool flag, UW row_count_since_gap)
{
	RowRingEntry entry;

	memcpy(entry.physical, row->physical, sizeof(entry.physical));
	entry.flag = flag;
	entry.row_count_since_gap = row_count_since_gap;
	score_and_detect_by_window_input_write(window_input, &entry);
}

/* Score each row and report where alarms start and end. */
LOCAL void score_and_detect_by_row_task(INT stacd, void *exinf)
{
	ScoreAndDetectByRowTask *task = exinf;
	DetectInstant state;
	ScoringRow scored;
	Row row;
	RecentRows rows_before; /* the rows before row, back to the last gap */
	INT ringing = 0, alarmed;
	UW last_no = 0, row_count_since_gap = 0;

	detect_instant_init(&state, THRESHOLD_SCORE, ALARM_K);
	recent_rows_clear(&rows_before);
	while (score_and_detect_by_row_input_read(task->score_and_detect_by_row_input, &row)
		== E_OK) {
		/*
		 * A row whose number is not one more than the last row's starts again from 0.
		 * Score and detect by window places its windows by this, as the PC does.
		 */
		if (recent_rows_count(&rows_before) > 0u && row.no == last_no + 1u) {
			row_count_since_gap++;
		} else {
			row_count_since_gap = 0;
			recent_rows_clear(&rows_before);
		}
		last_no = row.no;
		if (scoring_row(row.physical, &rows_before, active_model_mean,
			active_model_std, MIN_SPEED, &scored) != MODEL_OK) {
			break;
		}
		detect_instant_add_row(&state, row.no, scored.score, scored.rule_hit);
		alarmed = detect_instant_alarmed(&state);
		if (alarmed != ringing) {
			report_alarm_change(task->report_input, row.no, alarmed);
			ringing = alarmed;
		}
		pass_row_to_window(task->score_and_detect_by_window_input, &row,
			detect_instant_last_row_flagged(&state), row_count_since_gap);
		recent_rows_push(&rows_before, row.physical);
	}
	tk_ext_tsk();
}

EXPORT ER score_and_detect_by_row_task_create(ScoreAndDetectByRowTask *task,
	PRI priority, ScoreAndDetectByRowInput *score_and_detect_by_row_input,
	ReportInput *report_input,
	ScoreAndDetectByWindowInput *score_and_detect_by_window_input)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 2048, .task = score_and_detect_by_row_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};

	task->score_and_detect_by_row_input = score_and_detect_by_row_input;
	task->report_input = report_input;
	task->score_and_detect_by_window_input = score_and_detect_by_window_input;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER score_and_detect_by_row_task_start(ScoreAndDetectByRowTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
