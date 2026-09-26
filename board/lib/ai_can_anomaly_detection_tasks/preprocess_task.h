#ifndef PREPROCESS_TASK_H
#define PREPROCESS_TASK_H

#include <tk/tkernel.h>
#include "ai_can_anomaly_detection_tasks.h"
#include "slots.h"

/* What preprocess reads and where it sends the rows. */
typedef struct {
	Slots *slots;             /* what the CAN receive side writes */
	ID row_mbf;               /* where the rows go */
	ID task_id;               /* the task, for the tick to wake */
	ID tick_id;               /* the tick */
} PreprocessTask;

/* Create preprocess at priority, sending rows on row_mbf, and the tick that wakes it. */
IMPORT ER preprocess_task_create(PreprocessTask *task, PRI priority, ID row_mbf);

/* Start preprocess and its tick. */
IMPORT ER preprocess_task_start(PreprocessTask *task);

#endif
