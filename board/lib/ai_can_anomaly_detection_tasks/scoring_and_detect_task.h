#ifndef SCORING_AND_DETECT_TASK_H
#define SCORING_AND_DETECT_TASK_H

#include <tk/tkernel.h>
#include "ai_can_anomaly_detection_tasks.h"

/* Where scoring and detect gets rows and sends alarms, and what it counts. */
typedef struct {
	ID row_mbf;    /* where the rows come from */
	ID report_mbf; /* where the alarms go */
	ID task_id;
	TaskCounts *counts; /* where it counts rows */
} ScoringAndDetectTask;

/* The name of the model it scores with. */
IMPORT CONST char *CONST scoring_and_detect_model_id;

/* Create scoring and detect at priority, taking rows on row_mbf, alarms on report_mbf. */
IMPORT ER scoring_and_detect_task_create(ScoringAndDetectTask *task, PRI priority, ID row_mbf,
	ID report_mbf);

/* Start scoring and detect. */
IMPORT ER scoring_and_detect_task_start(ScoringAndDetectTask *task);

#endif
