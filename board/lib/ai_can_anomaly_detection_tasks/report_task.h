#ifndef REPORT_TASK_H
#define REPORT_TASK_H

#include <tk/tkernel.h>
#include "ai_can_anomaly_detection_tasks.h"
#include "report_input.h"

/* Where report gets alarms. */
typedef struct {
	ReportInput *report_input; /* where the alarms come from */
	ID task_id;
} ReportTask;

/* Create report at priority, taking alarms from report_input. */
IMPORT ER report_task_create(ReportTask *task, PRI priority, ReportInput *report_input);

/* Start report. */
IMPORT ER report_task_start(ReportTask *task);

#endif
