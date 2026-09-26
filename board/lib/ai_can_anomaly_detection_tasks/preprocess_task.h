#ifndef PREPROCESS_TASK_H
#define PREPROCESS_TASK_H

#include <tk/tkernel.h>
#include "ai_can_anomaly_detection_tasks.h"
#include "score_and_detect_by_row_input.h"
#include "slots.h"

/* What preprocess reads and where it sends the rows. */
typedef struct {
	Slots *slots;             /* what the CAN receive side writes */
	ScoreAndDetectByRowInput *score_and_detect_by_row_input; /* where the rows go */
	ID task_id;               /* the task, for the tick to wake */
	ID tick_id;               /* the tick */
} PreprocessTask;

/* Create preprocess and the tick that wakes it. Rows go to the input given. */
IMPORT ER preprocess_task_create(PreprocessTask *task, PRI priority,
	ScoreAndDetectByRowInput *score_and_detect_by_row_input);

/* Start preprocess and its tick. */
IMPORT ER preprocess_task_start(PreprocessTask *task);

#endif
