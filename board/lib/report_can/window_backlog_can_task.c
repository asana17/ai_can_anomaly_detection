#include <stdbool.h>
#include <string.h>
#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"
#include "window_backlog_can_task.h"

#define BACKLOG_BYTES 8u

/* value, or 0xFFFF when it does not fit in 2 bytes */
LOCAL UH at_most_two_bytes(UW value)
{
	if (value > 0xFFFFu) {
		return 0xFFFFu;
	}
	return (UH)value;
}

/*
 * The row's number little endian in bytes 0 to 3, the rows lost just before it in bytes
 * 4 and 5, then 0xFF.
 */
LOCAL void backlog_data(UB data[BACKLOG_BYTES], CONST WindowBacklog *window_backlog)
{
	UH missing_rows = at_most_two_bytes(window_backlog->missing_rows);
	UW i;

	memset(data, 0xFF, BACKLOG_BYTES);
	for (i = 0; i < 4u; i++) {
		data[i] = (UB)(window_backlog->no >> (8u * i));
	}
	data[4] = (UB)missing_rows;
	data[5] = (UB)(missing_rows >> 8);
}

/* Send the backlog frame with the task's ID. */
LOCAL void send_backlog(WindowBacklogCanTask *task, UB data[BACKLOG_BYTES])
{
	FDCAN_TxHeaderTypeDef header = {
		.Identifier = task->id, .IdType = FDCAN_EXTENDED_ID,
		.TxFrameType = FDCAN_DATA_FRAME, .DataLength = BACKLOG_BYTES,
		.ErrorStateIndicator = FDCAN_ESI_ACTIVE, .BitRateSwitch = FDCAN_BRS_OFF,
		.FDFormat = FDCAN_CLASSIC_CAN, .TxEventFifoControl = FDCAN_NO_TX_EVENTS,
		.MessageMarker = 0,
	};

	can_sender_send(task->sender, &header, data);
}

/* Send each backlog as one frame. */
LOCAL void window_backlog_can_task(INT stacd, void *exinf)
{
	WindowBacklogCanTask *task = exinf;
	WindowBacklog window_backlog;
	UB data[BACKLOG_BYTES];
	UW sent_no = 0;    /* the row of the backlog queued last */
	bool sent = false; /* a backlog has been queued */

	for (;;) {
		window_backlog_input_read(task->window_backlog_input, &window_backlog);
		/* a write just before the last read wakes report again with the same backlog */
		if (sent && window_backlog.no == sent_no) {
			continue;
		}
		sent_no = window_backlog.no;
		sent = true;
		backlog_data(data, &window_backlog);
		send_backlog(task, data);
	}
}

EXPORT ER window_backlog_can_task_create(WindowBacklogCanTask *task, PRI priority,
	WindowBacklogInput *window_backlog_input, CanSender *sender, UW id)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = window_backlog_can_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};

	task->window_backlog_input = window_backlog_input;
	task->sender = sender;
	task->id = id;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER window_backlog_can_task_start(WindowBacklogCanTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
