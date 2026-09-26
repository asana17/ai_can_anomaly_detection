#ifndef SCORE_AND_DETECT_BY_ROW_TASK_H
#define SCORE_AND_DETECT_BY_ROW_TASK_H

#include <tk/tkernel.h>
#include "ai_can_anomaly_detection_tasks.h"

/* Score and detect by row gives a verdict on every row. */

/* Where score and detect by row gets rows and sends alarms. */
typedef struct {
	ID row_mbf;    /* where the rows come from */
	ID report_mbf; /* where the alarms go */
	ID task_id;
} ScoreAndDetectByRowTask;

/* The name of the model it scores with. */
IMPORT CONST char *CONST score_and_detect_by_row_model_id;

/* Create score and detect by row. Rows come on row_mbf, alarms go on report_mbf. */
IMPORT ER score_and_detect_by_row_task_create(ScoreAndDetectByRowTask *task,
	PRI priority, ID row_mbf, ID report_mbf);

/* Start score and detect by row. */
IMPORT ER score_and_detect_by_row_task_start(ScoreAndDetectByRowTask *task);

#endif
