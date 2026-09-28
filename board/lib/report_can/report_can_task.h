#ifndef REPORT_CAN_TASK_H
#define REPORT_CAN_TASK_H

#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"
#include "report_input.h"

/* Where report over CAN gets alarms and sends them. */
typedef struct {
	ReportInput *report_input; /* where the alarms come from */
	FDCAN_HandleTypeDef *can;  /* the FDCAN the alarms go out on, started by the caller */
	ID task_id;
} ReportCanTask;

/* Create report over CAN at priority, taking alarms from report_input and sending on can. */
IMPORT ER report_can_task_create(ReportCanTask *task, PRI priority,
	ReportInput *report_input, FDCAN_HandleTypeDef *can);

/* Start report over CAN. */
IMPORT ER report_can_task_start(ReportCanTask *task);

#endif
