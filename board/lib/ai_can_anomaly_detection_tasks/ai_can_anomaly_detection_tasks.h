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
/* rows a flagged window ends on among the last DETECT_BY_ROW_RECENT_FLAGS the window alarm needs */
#define MIN_FLAGGED_WINDOWS_FOR_ALARM 1u
/* the ID the alarm is reported with, priority 3, PGN 0xFF00, source address 0x80 */
#define ALARM_ID 0x0CFF0080u
/* the ID the window alarm is reported with, priority 3, PGN 0xFF01, source address 0x80 */
#define WINDOW_ALARM_ID 0x0CFF0180u
/* the ID a stored record is reported with, priority 3, PGN 0xFF03, source address 0x80 */
#define STORED_RECORD_ID 0x0CFF0380u

/*
 * Create preprocess, score and detect by row, the copy of the alarm frames, and score and
 * detect by window on the slots and the frame ring. The alarm goes to report_input, the
 * window alarm to window_report_input and the alarm frames to store_alarm_frames_input,
 * all made by the caller.
 */
IMPORT ER ai_can_anomaly_detection_tasks_create(Slots *slots, FrameRing *frame_ring,
	ReportInput *report_input, ReportInput *window_report_input,
	StoreAlarmFramesInput *store_alarm_frames_input);

/* Start the tasks created. */
IMPORT ER ai_can_anomaly_detection_tasks_start(void);

#endif
