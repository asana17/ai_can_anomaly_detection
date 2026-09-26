#ifndef AI_CAN_ANOMALY_DETECTION_TASKS_H
#define AI_CAN_ANOMALY_DETECTION_TASKS_H

#include <tk/tkernel.h>
#include "model.h"
#include "slots.h"

#define MIN_SPEED 5.0f /* Settings.MIN_SPEED in common/settings.py */
#define ALARM_K 10u /* flagged rows among the last DETECT_INSTANT_ROWS an alarm needs */

/* Create preprocess, score and detect by row, and report on the slots. */
IMPORT ER ai_can_anomaly_detection_tasks_create(Slots *slots);

/* Start the tasks created. */
IMPORT ER ai_can_anomaly_detection_tasks_start(void);

#endif
