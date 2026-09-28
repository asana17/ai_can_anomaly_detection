#include <string.h>
#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"
#include "report_can_task.h"

#define ALARM_A_ID 0x0CFF0080u /* priority 3, PGN 0xFF00, source address 0x80 */
#define ALARM_BYTES 8u
#define ALARM_ROW_BYTES 4u
/* the 3 elements of the transmit FIFO */
#define ALL_TX_BUFFERS (FDCAN_TX_BUFFER0 | FDCAN_TX_BUFFER1 | FDCAN_TX_BUFFER2)

/* The state in byte 0, the row number little endian in bytes 1 to 4, then 0xFF. */
LOCAL void alarm_data(UB data[ALARM_BYTES], CONST Report *report)
{
	UW i;

	memset(data, 0xFF, ALARM_BYTES);
	data[0] = (UB)report->alarm;
	for (i = 0; i < ALARM_ROW_BYTES; i++) {
		data[1u + i] = (UB)(report->no >> (8u * i));
	}
}

/*
 * Send the alarm frame. When the transmit FIFO is full, it holds only older states,
 * so they are cancelled to make room for the latest. If the FIFO is still full, this
 * frame is not sent.
 */
LOCAL void send_alarm(FDCAN_HandleTypeDef *can, UB data[ALARM_BYTES])
{
	FDCAN_TxHeaderTypeDef header = {
		.Identifier = ALARM_A_ID, .IdType = FDCAN_EXTENDED_ID,
		.TxFrameType = FDCAN_DATA_FRAME, .DataLength = ALARM_BYTES,
		.ErrorStateIndicator = FDCAN_ESI_ACTIVE, .BitRateSwitch = FDCAN_BRS_OFF,
		.FDFormat = FDCAN_CLASSIC_CAN, .TxEventFifoControl = FDCAN_NO_TX_EVENTS,
		.MessageMarker = 0,
	};

	if (HAL_FDCAN_GetTxFifoFreeLevel(can) == 0u) {
		HAL_FDCAN_AbortTxRequest(can, ALL_TX_BUFFERS);
	}
	HAL_FDCAN_AddMessageToTxFifoQ(can, &header, data);
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
		send_alarm(task->can, data);
	}
}

EXPORT ER report_can_task_create(ReportCanTask *task, PRI priority,
	ReportInput *report_input, FDCAN_HandleTypeDef *can)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = report_can_task, .exinf = task,
		.tskatr = TA_HLNG | TA_RNG3,
	};

	task->report_input = report_input;
	task->can = can;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER report_can_task_start(ReportCanTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
