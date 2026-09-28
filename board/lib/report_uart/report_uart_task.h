#ifndef REPORT_UART_TASK_H
#define REPORT_UART_TASK_H

#include <tk/tkernel.h>
#include "report_input.h"

/* Where report over UART gets alarms. */
typedef struct {
	ReportInput *report_input; /* where the alarms come from */
	ID task_id;
} ReportUartTask;

/* Create report over UART at priority, taking alarms from report_input. */
IMPORT ER report_uart_task_create(ReportUartTask *task, PRI priority,
	ReportInput *report_input);

/* Start report over UART. */
IMPORT ER report_uart_task_start(ReportUartTask *task);

#endif
