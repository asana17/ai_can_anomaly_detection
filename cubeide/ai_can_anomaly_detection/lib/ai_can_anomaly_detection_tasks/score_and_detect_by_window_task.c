#include <tk/tkernel.h>
#include "detect_by_row.h"
#include "scale.h"
#include "scoring_error.h"
#include "section_cycles.h"
#include "signals.h"
#include "window_model_config.h"
#include "window_model_run.h"
#include "window_threshold.h"
#include "score_and_detect_by_window_task.h"

/* Hand report the row the window alarm starts or ends on. */
LOCAL void report_window_alarm_change(ReportInput *window_report_input,
	CONST RowRingEntry *entry, INT alarm)
{
	Report report = {0};

	report.no = entry->no;
	report.tick_ms = entry->tick_ms;
	report.alarm = alarm;
	report_input_write(window_report_input, &report);
}

/*
 * Tell the task that copies the alarm frames the row the window alarm starts on, and the
 * frames score and detect by row chose for it.
 */
LOCAL void pass_window_alarm_frame_positions(
	CopyAlarmFramesInput *copy_window_alarm_frames_input, CONST RowRingEntry *entry)
{
	AlarmFramePositions positions;

	positions.alarm = ALARM_KIND_WINDOW_ALARM;
	positions.no = entry->no;
	positions.frames_start = entry->frames_start;
	positions.frames_end = entry->frames_end;
	copy_alarm_frames_input_write(copy_window_alarm_frames_input, &positions);
}

/*
 * The rows lost just before entry. Rows are lost only when the ring overwrites them, which
 * leaves a jump in row_count_since_gap. A row with a smaller count than the row taken
 * before starts a new run, and the rows of that run before it were lost.
 */
LOCAL UW missing_rows_before(CONST RowRingEntry *entry, bool taken_before,
	UW last_count_since_gap)
{
	if (!taken_before) {
		return 0;
	}
	if (entry->row_count_since_gap > last_count_since_gap) {
		return entry->row_count_since_gap - last_count_since_gap - 1u;
	}
	return entry->row_count_since_gap;
}

/* Hand report the row no, with the rows lost just before it. */
LOCAL void report_backlog(WindowBacklogInput *window_backlog_input, UW no, UW missing_rows)
{
	WindowBacklog window_backlog;

	window_backlog.no = no;
	window_backlog.missing_rows = missing_rows;
	window_backlog_input_write(window_backlog_input, &window_backlog);
}

/*
 * Score the complete window: z-score each row with the window model's scale, run the
 * model, and take the error on the last row, as the PC does.
 */
LOCAL ModelStatus score_window(ScoreAndDetectByWindowTask *task, float *score,
	uint32_t *cycles)
{
	UW row;
	ModelStatus error;
	CONST UW last = (WINDOW_MODEL_ROWS - 1u) * SIGNAL_COUNT;

	for (row = 0; row < WINDOW_MODEL_ROWS; row++) {
		scale_row(row_ring_as_window_entry(&task->row_ring_as_window, row)->physical,
			window_model_mean, window_model_std, &task->scaled[row * SIGNAL_COUNT],
			SIGNAL_COUNT);
	}
	error = window_model_run(task->scaled, task->reconstructed, cycles);
	if (error != MODEL_OK) {
		return error;
	}
	*score = scoring_error(&task->scaled[last], &task->reconstructed[last], SIGNAL_COUNT);
	return MODEL_OK;
}

/* What score and detect by window carries from one row to the next. */
typedef struct {
	DetectByRow state;
	INT ringing;
	UW last_count_since_gap; /* row_count_since_gap of the last row taken */
	bool taken_before;       /* a row has been taken */
} WindowProgress;

/*
 * End the stretch of rows at a gap, where the PC's window alarm ends as its count starts
 * again.
 */
LOCAL void end_window_rows(ScoreAndDetectByWindowTask *task, WindowProgress *progress,
	CONST RowRingEntry *entry)
{
	detect_by_row_clear_ring(&progress->state);
	if (progress->ringing) {
		report_window_alarm_change(task->window_report_input, entry, 0);
		progress->ringing = 0;
	}
}

/*
 * Add the row to the window, and score the window when it is complete. A row is flagged
 * when the window ending on it scores above the threshold, and a row no window ends on is
 * not. The window alarm rings while enough of the last rows are flagged, as on the PC. On
 * rows the alarm by row rings on, the window is not scored and the window alarm stays
 * silent. more_in_ring tells that a row read with this one waits after it.
 */
LOCAL void score_and_detect_window_row(ScoreAndDetectByWindowTask *task,
	WindowProgress *progress, CONST RowRingEntry *entry, bool more_in_ring)
{
	INT alarmed;
	bool flagged;
	float score;
	uint32_t cycles;
	UW missing_rows;
	bool waiting; /* the next row came before this one was done */

	missing_rows = missing_rows_before(entry, progress->taken_before,
		progress->last_count_since_gap);
	row_ring_as_window_push(&task->row_ring_as_window, entry);
	flagged = false;
	if (row_ring_as_window_is_complete(&task->row_ring_as_window)
		&& !entry->alarm_ringing) {
		if (score_window(task, &score, &cycles) == MODEL_OK) {
			section_cycles_add(SECTION_WINDOW_MODEL, cycles);
			flagged = detect_by_row_flagged(score, WINDOW_THRESHOLD_SCORE, false);
		} else {
			tk_ext_tsk();
		}
	}
	progress->last_count_since_gap = entry->row_count_since_gap;
	progress->taken_before = true;
	waiting = more_in_ring || score_and_detect_by_window_input_has_rows(
		task->score_and_detect_by_window_input);
	if (waiting || missing_rows > 0u) {
		report_backlog(task->window_backlog_input, entry->no, missing_rows);
	}
	detect_by_row_push_flag(&progress->state, entry->no, flagged);
	alarmed = detect_by_row_alarmed(&progress->state) && !entry->alarm_ringing;
	if (alarmed != progress->ringing) {
		report_window_alarm_change(task->window_report_input, entry, alarmed);
		progress->ringing = alarmed;
		if (alarmed) {
			pass_window_alarm_frame_positions(task->copy_window_alarm_frames_input,
				entry);
		}
	}
}

/* Take each row read, or the gap after the last row. */
LOCAL void score_and_detect_by_window_task(INT stacd, void *exinf)
{
	ScoreAndDetectByWindowTask *task = exinf;
	WindowProgress progress;
	CONST RowRingEntry *entry;
	UW index, started;

	detect_by_row_init(&progress.state, MIN_FLAGGED_WINDOWS_FOR_ALARM);
	progress.ringing = 0;
	progress.last_count_since_gap = 0;
	progress.taken_before = false;
	row_ring_as_window_clear(&task->row_ring_as_window);
	for (;;) {
		score_and_detect_by_window_input_read(task->score_and_detect_by_window_input,
			&task->row_ring);
		for (index = 0; index < row_ring_count(&task->row_ring); index++) {
			started = section_cycles_start();
			entry = row_ring_entry(&task->row_ring, index);
			if (entry->gap) {
				end_window_rows(task, &progress, entry);
			} else {
				score_and_detect_window_row(task, &progress, entry,
					index + 1u < row_ring_count(&task->row_ring));
			}
			section_cycles_end(SECTION_SCORE_AND_DETECT_BY_WINDOW, started);
		}
	}
}

EXPORT ER score_and_detect_by_window_task_create(ScoreAndDetectByWindowTask *task,
	PRI priority, ScoreAndDetectByWindowInput *score_and_detect_by_window_input,
	ReportInput *window_report_input, WindowBacklogInput *window_backlog_input,
	CopyAlarmFramesInput *copy_window_alarm_frames_input)
{
	/* The stack holds the st-ai inference, as score and detect by row's does. */
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 3072, .task = score_and_detect_by_window_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};

	task->score_and_detect_by_window_input = score_and_detect_by_window_input;
	task->window_report_input = window_report_input;
	task->window_backlog_input = window_backlog_input;
	task->copy_window_alarm_frames_input = copy_window_alarm_frames_input;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER score_and_detect_by_window_task_start(ScoreAndDetectByWindowTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
