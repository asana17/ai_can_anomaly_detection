#include <string.h>
#include <tk/tkernel.h>
#include "detect_by_row.h"
#include "model.h"
#include "model_config.h"
#include "recent_rows.h"
#include "scoring.h"
#include "section_cycles.h"
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

/*
 * The row and the frames behind the last ALARM_FRAMES_ROWS rows, or fewer since the last
 * gap, for the task that copies the alarm frames if an alarm starts on the row.
 */
LOCAL void alarm_frame_positions(CONST Row *row,
	CONST UW frames_starts[ALARM_FRAMES_ROWS], UW row_count_since_gap,
	AlarmFramePositions *positions)
{
	UW rows_back = ALARM_FRAMES_ROWS - 1u;

	if (row_count_since_gap < rows_back) {
		rows_back = row_count_since_gap;
	}
	positions->alarm = ALARM_KIND_ALARM;
	positions->no = row->no;
	positions->frames_start = frames_starts[(row->no - rows_back) % ALARM_FRAMES_ROWS];
	positions->frames_end = row->frames_end;
}

/*
 * Hand score and detect by window the row, whether the alarm rings on it, its count since
 * the last gap and the positions of the frames to store if the window alarm starts on it.
 */
LOCAL void pass_row_to_window(ScoreAndDetectByWindowInput *window_input, CONST Row *row,
	INT ringing, UW row_count_since_gap, CONST AlarmFramePositions *positions)
{
	RowRingEntry entry;

	entry.no = row->no;
	entry.tick_ms = row->tick_ms;
	memcpy(entry.physical, row->physical, sizeof(entry.physical));
	entry.alarm_ringing = ringing != 0;
	entry.row_count_since_gap = row_count_since_gap;
	entry.frames_start = positions->frames_start;
	entry.frames_end = positions->frames_end;
	score_and_detect_by_window_input_write(window_input, &entry);
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
	UW last_no = 0, row_count_since_gap = 0, started;
	UW frames_starts[ALARM_FRAMES_ROWS]; /* each recent row's frames_start */
	AlarmFramePositions positions;

	detect_by_row_init(&state, MIN_FLAGGED_FOR_ALARM);
	recent_rows_clear(&rows_before);
	while (score_and_detect_by_row_input_read(task->score_and_detect_by_row_input, &row)
		== E_OK) {
		started = section_cycles_start();
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
		alarm_frame_positions(&row, frames_starts, row_count_since_gap, &positions);
		if (scoring_row(row.physical, &rows_before, instant_model_mean,
			instant_model_std, MIN_SPEED, &scored) != MODEL_OK) {
			break;
		}
		section_cycles_add(SECTION_ROW_MODEL, scored.cycles);
		flagged = detect_by_row_flagged(scored.score, THRESHOLD_SCORE, scored.rule_hit);
		detect_by_row_push_flag(&state, row.no, flagged);
		alarmed = detect_by_row_alarmed(&state);
		if (alarmed != ringing) {
			report_alarm_change(task->report_input, &row, alarmed);
			ringing = alarmed;
			if (alarmed) {
				copy_alarm_frames_input_write(task->copy_alarm_frames_input,
					&positions);
			}
		}
		pass_row_to_window(task->score_and_detect_by_window_input, &row,
			ringing, row_count_since_gap, &positions);
		recent_rows_push(&rows_before, row.physical);
		section_cycles_end(SECTION_SCORE_AND_DETECT_BY_ROW, started);
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
