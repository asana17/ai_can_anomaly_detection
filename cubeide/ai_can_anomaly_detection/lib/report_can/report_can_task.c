#include <string.h>
#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"
#include "report_can_task.h"

#define ALARM_BYTES 8u
#define ALARM_ROW_BYTES 4u

/* The ms from the report's tick to now, or 0xFFFF when it does not fit in 2 bytes. */
LOCAL UH ms_since_tick(CONST Report *report)
{
	SYSTIM now;
	UW ms;

	tk_get_otm(&now);
	ms = now.lo - report->tick_ms;
	if (ms > 0xFFFFu) {
		return 0xFFFFu;
	}
	return (UH)ms;
}

/*
 * The state in byte 0, the row number little endian in bytes 1 to 4, the ms from the
 * row's tick little endian in bytes 5 and 6, then 0xFF.
 */
LOCAL void alarm_data(UB data[ALARM_BYTES], CONST Report *report)
{
	UH ms = ms_since_tick(report);
	UW i;

	memset(data, 0xFF, ALARM_BYTES);
	data[0] = (UB)report->alarm;
	for (i = 0; i < ALARM_ROW_BYTES; i++) {
		data[1u + i] = (UB)(report->no >> (8u * i));
	}
	data[5] = (UB)ms;
	data[6] = (UB)(ms >> 8);
}

/* Send the alarm frame with the task's ID. */
LOCAL void send_alarm(ReportCanTask *task, UB data[ALARM_BYTES])
{
	FDCAN_TxHeaderTypeDef header = {
		.Identifier = task->id, .IdType = FDCAN_EXTENDED_ID,
		.TxFrameType = FDCAN_DATA_FRAME, .DataLength = ALARM_BYTES,
		.ErrorStateIndicator = FDCAN_ESI_ACTIVE, .BitRateSwitch = FDCAN_BRS_OFF,
		.FDFormat = FDCAN_CLASSIC_CAN, .TxEventFifoControl = FDCAN_NO_TX_EVENTS,
		.MessageMarker = 0,
	};

	can_sender_send(task->sender, &header, data);
}

/* Send each start and end of the alarm as one frame. */
LOCAL void report_can_task(INT stacd, void *exinf)
{
	ReportCanTask *task = exinf;
	Report report;
	UB data[ALARM_BYTES];
	INT sent = 0; /* the alarm state queued last, not ringing at first */

	for (;;) {
		report_input_read(task->report_input, &report);
		/* a write just before the last read wakes report again with the same state */
		if (report.alarm == sent) {
			continue;
		}
		sent = report.alarm;
		alarm_data(data, &report);
		send_alarm(task, data);
	}
}

EXPORT ER report_can_task_create(ReportCanTask *task, PRI priority,
	ReportInput *report_input, CanSender *sender, UW id)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = report_can_task, .exinf = task,
		.tskatr = TA_HLNG | TA_RNG3,
	};

	task->report_input = report_input;
	task->sender = sender;
	task->id = id;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER report_can_task_start(ReportCanTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
