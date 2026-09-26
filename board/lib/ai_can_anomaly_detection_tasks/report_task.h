#ifndef REPORT_TASK_H
#define REPORT_TASK_H

#include <tk/tkernel.h>
#include "ai_can_anomaly_detection_tasks.h"

/* Where report gets alarms. */
typedef struct {
	ID report_mbf;          /* where the alarms come from */
	ID task_id;
	CONST char *model_id;   /* the model score and detect by row runs */
} ReportTask;

/* Create report at priority, taking alarms on report_mbf. */
IMPORT ER report_task_create(ReportTask *task, PRI priority, ID report_mbf);

/* Start report. */
IMPORT ER report_task_start(ReportTask *task);

#endif
