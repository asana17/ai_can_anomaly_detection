#ifndef AI_CAN_ANOMALY_DETECTION_TASKS_H
#define AI_CAN_ANOMALY_DETECTION_TASKS_H

#include <tk/tkernel.h>
#include "model.h"
#include "slots.h"

#define MIN_SPEED 5.0f /* Settings.MIN_SPEED in common/settings.py */
#define ALARM_K 10u /* flagged rows among the last DETECT_INSTANT_ROWS an alarm needs */

/* What preprocess sends scoring and detect. */
typedef struct {
	UW no;
	float physical[MODEL_SIGNALS];
} Row;

/* What scoring and detect sends report. */
typedef struct {
	UW no;
	UW score_bits; /* float32 score bits; avoids UART float formatting. */
	INT alarm; /* the row starts an alarm, or ends the one that was ringing */
	INT rule;
	ModelStatus error;
} Report;

/* Create preprocess, scoring and detect, and report on the slots. */
IMPORT ER ai_can_anomaly_detection_tasks_create(Slots *slots);

/* Start the tasks created. */
IMPORT ER ai_can_anomaly_detection_tasks_start(void);

#endif
