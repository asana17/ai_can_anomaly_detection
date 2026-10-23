#ifndef REPORT_CAN_TASK_H
#define REPORT_CAN_TASK_H

#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"
#include "can_sender.h"
#include "report_input.h"

/* Where report over CAN gets alarms and sends them. */
typedef struct {
	ReportInput *report_input; /* where the alarms come from */
	CanSender *sender;         /* what sends the alarm frames */
	UW id;                     /* the ID the alarm frames go out with */
	ID task_id;
} ReportCanTask;

/*
 * Create report over CAN at priority, taking alarms from report_input and sending them on
 * sender with id. Reports over CAN on one FDCAN each need their own id.
 */
IMPORT ER report_can_task_create(ReportCanTask *task, PRI priority,
	ReportInput *report_input, CanSender *sender, UW id);

/* Start report over CAN. */
IMPORT ER report_can_task_start(ReportCanTask *task);

#endif
