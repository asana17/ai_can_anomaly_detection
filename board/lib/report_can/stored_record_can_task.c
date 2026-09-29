#include <stdbool.h>
#include <string.h>
#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"
#include "stored_record_can_task.h"

#define RECORD_BYTES 8u

/*
 * The row alarm A started on little endian in bytes 0 to 3, the frame count in bytes 4
 * and 5, then 0xFF.
 */
LOCAL void record_data(UB data[RECORD_BYTES], CONST StoredRecord *stored_record)
{
	UW i;

	memset(data, 0xFF, RECORD_BYTES);
	for (i = 0; i < 4u; i++) {
		data[i] = (UB)(stored_record->no >> (8u * i));
	}
	data[4] = (UB)stored_record->frame_count;
	data[5] = (UB)(stored_record->frame_count >> 8);
}

/* Send the record frame with the task's ID. */
LOCAL void send_record(StoredRecordCanTask *task, UB data[RECORD_BYTES])
{
	FDCAN_TxHeaderTypeDef header = {
		.Identifier = task->id, .IdType = FDCAN_EXTENDED_ID,
		.TxFrameType = FDCAN_DATA_FRAME, .DataLength = RECORD_BYTES,
		.ErrorStateIndicator = FDCAN_ESI_ACTIVE, .BitRateSwitch = FDCAN_BRS_OFF,
		.FDFormat = FDCAN_CLASSIC_CAN, .TxEventFifoControl = FDCAN_NO_TX_EVENTS,
		.MessageMarker = 0,
	};

	can_sender_send(task->sender, &header, data);
}

/* Send each record written to Flash as one frame. */
LOCAL void stored_record_can_task(INT stacd, void *exinf)
{
	StoredRecordCanTask *task = exinf;
	StoredRecord stored_record;
	UB data[RECORD_BYTES];
	UW sent_no = 0;    /* the row of the record queued last */
	bool sent = false; /* a record has been queued */

	for (;;) {
		stored_record_input_read(task->stored_record_input, &stored_record);
		/* a write just before the last read wakes report again with the same record */
		if (sent && stored_record.no == sent_no) {
			continue;
		}
		sent_no = stored_record.no;
		sent = true;
		record_data(data, &stored_record);
		send_record(task, data);
	}
}

EXPORT ER stored_record_can_task_create(StoredRecordCanTask *task, PRI priority,
	StoredRecordInput *stored_record_input, CanSender *sender, UW id)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = stored_record_can_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};

	task->stored_record_input = stored_record_input;
	task->sender = sender;
	task->id = id;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER stored_record_can_task_start(StoredRecordCanTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
