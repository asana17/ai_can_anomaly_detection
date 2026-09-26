#ifndef REPORT_TASK_H
#define REPORT_TASK_H

#include <tk/tkernel.h>
#include "ai_can_anomaly_detection_tasks.h"
#include "slots.h"

/* Where report gets alarms, and the counts it prints at the end. */
typedef struct {
	ID report_mbf;          /* where the alarms come from */
	ID task_id;
	CONST char *model_id;   /* the model scoring and detect runs */
	CONST Slots *slots;     /* for the frames they took */
	CONST TaskCounts *counts;
} ReportTask;

/* Create report at priority, taking alarms on report_mbf. */
IMPORT ER report_task_create(ReportTask *task, PRI priority, ID report_mbf);

/* Start report. */
IMPORT ER report_task_start(ReportTask *task);

#endif
