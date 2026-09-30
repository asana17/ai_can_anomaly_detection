#include <tk/tkernel.h>
#include "moving.h"
#include "preprocess_task.h"
#include "section_cycles.h"
#include "ai_can_anomaly_detection_tasks.h"

#define PERIOD 100 /* ms between rows, Settings.PERIOD */
#define MAX_HOLD_ROWS 10u /* rows with no frame that end a stretch, Settings.MAX_HOLD */

LOCAL void preprocess_tick(void *exinf)
{
	UW started = section_cycles_start();

	tk_wup_tsk(((PreprocessTask *)exinf)->task_id);
	section_cycles_end(SECTION_TICK, started);
}

/*
 * Fill row's physical values from the slots. FALSE when no row goes on this tick: no frame
 * came since the tick before, a PGN has not arrived yet, or the truck is not moving.
 * seen and quiet carry the slots' frame count and the ticks with no frame across ticks.
 */
LOCAL BOOL build_row(PreprocessTask *task, UW *seen, UW *quiet, Row *row)
{
	SignalState held;
	UW frames, intsts, i;

	DI(intsts);
	frames = task->slots->frames;
	EI(intsts);
	if (frames == *seen) {
		(*quiet)++;
	} else {
		*seen = frames;
		*quiet = 0;
	}
	if (*quiet == MAX_HOLD_ROWS) {
		/* what the slots hold predates the gap, as grid_sample drops it */
		DI(intsts);
		signal_state_clear(&task->slots->state);
		EI(intsts);
	}
	if (*quiet > 0) {
		/* no frame since the last tick, so the row would hold only old values */
		return FALSE;
	}
	for (i = 0; i < SIGNAL_STATE_SLOTS; i++) {
		DI(intsts);
		held.slots[i] = task->slots->state.slots[i];
		EI(intsts);
	}
	if (!signal_state_ready(&held)) {
		return FALSE;
	}
	signal_state_row(&held, row->physical);
	return moving(row->physical, MIN_SPEED);
}

/* Build a row from the slots on each tick, and send it on when the truck moves. */
LOCAL void preprocess_task(INT stacd, void *exinf)
{
	PreprocessTask *task = exinf;
	Row row;
	UW number = 0, seen = 0, quiet = 0;
	UW frames_start, frames_end = 0, started;
	SYSTIM woke;

	while (tk_slp_tsk(TMO_FEVR) == E_OK) {
		started = section_cycles_start();
		number++;
		tk_get_otm(&woke);
		/* the frames since the tick before, which a row built now reflects */
		frames_start = frames_end;
		frames_end = task->frame_ring->position;
		if (build_row(task, &seen, &quiet, &row)) {
			row.no = number;
			row.tick_ms = woke.lo;
			row.frames_start = frames_start;
			row.frames_end = frames_end;
			if (score_and_detect_by_row_input_write(task->score_and_detect_by_row_input,
				&row) != E_OK) {
				break;
			}
		}
		section_cycles_end(SECTION_PREPROCESS, started);
	}
	tk_ext_tsk();
}

EXPORT ER preprocess_task_create(PreprocessTask *task, PRI priority,
	ScoreAndDetectByRowInput *score_and_detect_by_row_input)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = preprocess_task, .exinf = task,
		.tskatr = TA_HLNG | TA_RNG3,
	};
	T_CCYC ccyc = {
		.cycatr = TA_HLNG, .cychdr = (FP)preprocess_tick, .exinf = task,
		.cyctim = PERIOD, .cycphs = PERIOD,
	};

	task->score_and_detect_by_row_input = score_and_detect_by_row_input;
	task->task_id = tk_cre_tsk(&ctsk);
	if (task->task_id < E_OK) {
		return task->task_id;
	}
	task->tick_id = tk_cre_cyc(&ccyc);
	if (task->tick_id < E_OK) {
		return task->tick_id;
	}
	return E_OK;
}

EXPORT ER preprocess_task_start(PreprocessTask *task)
{
	ER error;

	error = tk_sta_tsk(task->task_id, 0);
	if (error < E_OK) {
		return error;
	}
	return tk_sta_cyc(task->tick_id);
}
