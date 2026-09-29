#ifndef STORED_RECORD_UART_TASK_H
#define STORED_RECORD_UART_TASK_H

#include <tk/tkernel.h>
#include "stored_record_input.h"

/* Where the stored record report over UART gets records. */
typedef struct {
	StoredRecordInput *stored_record_input; /* where the records come from */
	UW id;                                  /* the ID each line names the record by */
	ID task_id;
} StoredRecordUartTask;

/*
 * Create the stored record report over UART at priority, taking records from
 * stored_record_input and printing them with id.
 */
IMPORT ER stored_record_uart_task_create(StoredRecordUartTask *task, PRI priority,
	StoredRecordInput *stored_record_input, UW id);

/* Start the stored record report over UART. */
IMPORT ER stored_record_uart_task_start(StoredRecordUartTask *task);

#endif
