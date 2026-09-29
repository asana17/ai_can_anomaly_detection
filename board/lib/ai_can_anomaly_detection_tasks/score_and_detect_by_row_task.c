#include <string.h>
#include <tk/tkernel.h>
#include "detect_by_row.h"
#include "model.h"
#include "model_config.h"
#include "recent_rows.h"
#include "scoring.h"
#include "score_and_detect_by_row_task.h"
#include "ai_can_anomaly_detection_tasks.h"
#include "threshold.h"

/* Hand report the row an alarm starts or ends on. */
LOCAL void report_alarm_change(ReportInput *report_input, CONST Row *row, INT alarm)
{
	Report report = {0};

	report.no = row->no;
	report.tick_ms = row->tick_ms;
	report.alarm = alarm;
	report_input_write(report_input, &report);
}

/* Hand score and detect by window the row, its flag and its count since the last gap. */
LOCAL void pass_row_to_window(ScoreAndDetectByWindowInput *window_input, CONST Row *row,
	bool flag, UW row_count_since_gap)
{
	RowRingEntry entry;

	entry.no = row->no;
	entry.tick_ms = row->tick_ms;
	memcpy(entry.physical, row->physical, sizeof(entry.physical));
	entry.flag = flag;
	entry.row_count_since_gap = row_count_since_gap;
	score_and_detect_by_window_input_write(window_input, &entry);
}

/*
 * Tell the task that copies the alarm frames the row an alarm starts on, and the frames
 * behind the last ALARM_FRAMES_ROWS rows, or fewer since the last gap.
 */
LOCAL void pass_alarm_frame_positions(CopyAlarmFramesInput *copy_alarm_frames_input,
	CONST Row *row, CONST UW frames_starts[ALARM_FRAMES_ROWS],
	UW row_count_since_gap)
{
	AlarmFramePositions positions;
	UW rows_back = ALARM_FRAMES_ROWS - 1u;

	if (row_count_since_gap < rows_back) {
		rows_back = row_count_since_gap;
	}
	positions.no = row->no;
	positions.frames_start = frames_starts[(row->no - rows_back) % ALARM_FRAMES_ROWS];
	positions.frames_end = row->frames_end;
	copy_alarm_frames_input_write(copy_alarm_frames_input, &positions);
}

/* Score each row and report where alarms start and end. */
LOCAL void score_and_detect_by_row_task(INT stacd, void *exinf)
{
	ScoreAndDetectByRowTask *task = exinf;
	DetectByRow state;
	ScoringRow scored;
	Row row;
	RecentRows rows_before; /* the rows before row, back to the last gap */
	INT ringing = 0, alarmed;
	bool flagged;
	UW last_no = 0, row_count_since_gap = 0;
	UW frames_starts[ALARM_FRAMES_ROWS]; /* each recent row's frames_start */

	detect_by_row_init(&state, MIN_FLAGGED_FOR_ALARM);
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
		frames_starts[row.no % ALARM_FRAMES_ROWS] = row.frames_start;
		if (scoring_row(row.physical, &rows_before, instant_model_mean,
			instant_model_std, MIN_SPEED, &scored) != MODEL_OK) {
			break;
		}
		flagged = detect_by_row_flagged(scored.score, THRESHOLD_SCORE, scored.rule_hit);
		detect_by_row_push_flag(&state, row.no, flagged);
		alarmed = detect_by_row_alarmed(&state);
		if (alarmed != ringing) {
			report_alarm_change(task->report_input, &row, alarmed);
			ringing = alarmed;
			if (alarmed) {
				pass_alarm_frame_positions(task->copy_alarm_frames_input, &row,
					frames_starts, row_count_since_gap);
			}
		}
		pass_row_to_window(task->score_and_detect_by_window_input, &row,
			flagged, row_count_since_gap);
		recent_rows_push(&rows_before, row.physical);
	}
	tk_ext_tsk();
}

EXPORT ER score_and_detect_by_row_task_create(ScoreAndDetectByRowTask *task,
	PRI priority, ScoreAndDetectByRowInput *score_and_detect_by_row_input,
	ReportInput *report_input,
	ScoreAndDetectByWindowInput *score_and_detect_by_window_input,
	CopyAlarmFramesInput *copy_alarm_frames_input)
{
	/* The stack holds rows_before, RECENT_ROWS_ROWS rows of SIGNAL_COUNT floats. */
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 3072, .task = score_and_detect_by_row_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};

	task->score_and_detect_by_row_input = score_and_detect_by_row_input;
	task->report_input = report_input;
	task->score_and_detect_by_window_input = score_and_detect_by_window_input;
	task->copy_alarm_frames_input = copy_alarm_frames_input;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER score_and_detect_by_row_task_start(ScoreAndDetectByRowTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
