#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "report_uart_task.h"

/* Print each alarm over UART. */
LOCAL void report_uart_task(INT stacd, void *exinf)
{
	ReportUartTask *task = exinf;
	Report report;
	INT shown = 0; /* the alarm state printed last, not ringing at first */

	for (;;) {
		report_input_read(task->report_input, &report);
		/* a write just before the last read wakes report again with the same state */
		if (report.alarm == shown) {
			continue;
		}
		shown = report.alarm;
		if (report.alarm) {
			tm_printf((UB*)"alarm 0x%08X start at row %u\n", task->id, report.no);
		} else {
			tm_printf((UB*)"alarm 0x%08X end at row %u\n", task->id, report.no);
		}
	}
}

EXPORT ER report_uart_task_create(ReportUartTask *task, PRI priority,
	ReportInput *report_input, UW id)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = report_uart_task, .exinf = task,
		.tskatr = TA_HLNG | TA_RNG3,
	};

	task->report_input = report_input;
	task->id = id;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER report_uart_task_start(ReportUartTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
