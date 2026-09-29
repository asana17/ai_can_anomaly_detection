#include <stdbool.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "stored_record_uart_task.h"

/* Print each record written to Flash over UART. */
LOCAL void stored_record_uart_task(INT stacd, void *exinf)
{
	StoredRecordUartTask *task = exinf;
	StoredRecord stored_record;
	UW shown_no = 0;    /* the row of the record printed last */
	bool shown = false; /* a record has been printed */

	for (;;) {
		stored_record_input_read(task->stored_record_input, &stored_record);
		/* a write just before the last read wakes report again with the same record */
		if (shown && stored_record.no == shown_no) {
			continue;
		}
		shown_no = stored_record.no;
		shown = true;
		tm_printf((UB*)"stored 0x%08X record of row %u with %u frames\n", task->id,
			stored_record.no, stored_record.frame_count);
	}
}

EXPORT ER stored_record_uart_task_create(StoredRecordUartTask *task, PRI priority,
	StoredRecordInput *stored_record_input, UW id)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = stored_record_uart_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};

	task->stored_record_input = stored_record_input;
	task->id = id;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER stored_record_uart_task_start(StoredRecordUartTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
