#include <stdbool.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "window_backlog_uart_task.h"

/* Print each backlog over UART. */
LOCAL void window_backlog_uart_task(INT stacd, void *exinf)
{
	WindowBacklogUartTask *task = exinf;
	WindowBacklog window_backlog;
	UW shown_no = 0;    /* the row of the backlog printed last */
	bool shown = false; /* a backlog has been printed */

	for (;;) {
		window_backlog_input_read(task->window_backlog_input, &window_backlog);
		/* a write just before the last read wakes report again with the same backlog */
		if (shown && window_backlog.no == shown_no) {
			continue;
		}
		shown_no = window_backlog.no;
		shown = true;
		tm_printf((UB*)"backlog 0x%08X at row %u, %u rows lost before it\n", task->id,
			window_backlog.no, window_backlog.missing_rows);
	}
}

EXPORT ER window_backlog_uart_task_create(WindowBacklogUartTask *task, PRI priority,
	WindowBacklogInput *window_backlog_input, UW id)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = window_backlog_uart_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};

	task->window_backlog_input = window_backlog_input;
	task->id = id;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER window_backlog_uart_task_start(WindowBacklogUartTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
