#ifndef STORED_RECORD_CAN_TASK_H
#define STORED_RECORD_CAN_TASK_H

#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"
#include "can_sender.h"
#include "stored_record_input.h"

/* Where the stored record report over CAN gets records and sends them. */
typedef struct {
	StoredRecordInput *stored_record_input; /* where the records come from */
	CanSender *sender;                      /* what sends the record frames */
	UW id;                                  /* the ID the record frames go out with */
	ID task_id;
} StoredRecordCanTask;

/*
 * Create the stored record report over CAN at priority, taking records from
 * stored_record_input and sending them on sender with id.
 */
IMPORT ER stored_record_can_task_create(StoredRecordCanTask *task, PRI priority,
	StoredRecordInput *stored_record_input, CanSender *sender, UW id);

/* Start the stored record report over CAN. */
IMPORT ER stored_record_can_task_start(StoredRecordCanTask *task);

#endif
