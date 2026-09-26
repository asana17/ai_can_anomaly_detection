#include <tk/tkernel.h>
#include "score_and_detect_by_window_task.h"

/* Add each row read to the window, and check whether the window is complete. */
LOCAL void score_and_detect_by_window_task(INT stacd, void *exinf)
{
	ScoreAndDetectByWindowTask *task = exinf;
	UW index;

	row_ring_as_window_clear(&task->row_ring_as_window);
	for (;;) {
		score_and_detect_by_window_input_read(task->score_and_detect_by_window_input,
			&task->row_ring);
		for (index = 0; index < row_ring_count(&task->row_ring); index++) {
			row_ring_as_window_push(&task->row_ring_as_window,
				row_ring_entry(&task->row_ring, index));
			if (row_ring_as_window_is_complete(&task->row_ring_as_window)) {
				/* TODO: score the window with the windowed model */
			}
		}
	}
}

EXPORT ER score_and_detect_by_window_task_create(ScoreAndDetectByWindowTask *task,
	PRI priority, ScoreAndDetectByWindowInput *score_and_detect_by_window_input)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = score_and_detect_by_window_task,
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
