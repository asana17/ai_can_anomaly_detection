#ifndef AI_CAN_ANOMALY_DETECTION_TASKS_H
#define AI_CAN_ANOMALY_DETECTION_TASKS_H

#include <tk/tkernel.h>
#include "model.h"
#include "frame_ring.h"
#include "report_input.h"
#include "slots.h"
#include "store_alarm_frames_input.h"

#define MIN_SPEED 5.0f /* Settings.MIN_SPEED in common/settings.py */
#define MIN_FLAGGED_FOR_ALARM 10u /* flagged rows among the last DETECT_BY_ROW_RECENT_FLAGS an alarm needs */
/* the ID the alarm is reported with, priority 3, PGN 0xFF00, source address 0x80 */
#define ALARM_ID 0x0CFF0080u

/*
 * Create preprocess, score and detect by row, the copy of the alarm frames, and score and
 * detect by window on the slots and the frame ring. Alarms go to report_input and the
 * alarm frames to store_alarm_frames_input, both made by the caller.
 */
IMPORT ER ai_can_anomaly_detection_tasks_create(Slots *slots, FrameRing *frame_ring,
	ReportInput *report_input, StoreAlarmFramesInput *store_alarm_frames_input);

/* Start the tasks created. */
IMPORT ER ai_can_anomaly_detection_tasks_start(void);

#endif
