#include <tk/tkernel.h>
#include "scale.h"
#include "scoring_error.h"
#include "signals.h"
#include "window_model_config.h"
#include "window_model_run.h"
#include "score_and_detect_by_window_task.h"

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

/* Add each row read to the window, and score the window when it is complete. */
LOCAL void score_and_detect_by_window_task(INT stacd, void *exinf)
{
	ScoreAndDetectByWindowTask *task = exinf;
	UW index;
	float score;
	uint32_t cycles;

	row_ring_as_window_clear(&task->row_ring_as_window);
	for (;;) {
		score_and_detect_by_window_input_read(task->score_and_detect_by_window_input,
			&task->row_ring);
		for (index = 0; index < row_ring_count(&task->row_ring); index++) {
			row_ring_as_window_push(&task->row_ring_as_window,
				row_ring_entry(&task->row_ring, index));
			if (row_ring_as_window_is_complete(&task->row_ring_as_window)
				&& score_window(task, &score, &cycles) != MODEL_OK) {
				tk_ext_tsk();
			}
		}
	}
}

EXPORT ER score_and_detect_by_window_task_create(ScoreAndDetectByWindowTask *task,
	PRI priority, ScoreAndDetectByWindowInput *score_and_detect_by_window_input)
{
	/* The stack holds the st-ai inference, as score and detect by row's does. */
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 3072, .task = score_and_detect_by_window_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};

	task->score_and_detect_by_window_input = score_and_detect_by_window_input;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER score_and_detect_by_window_task_start(ScoreAndDetectByWindowTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
