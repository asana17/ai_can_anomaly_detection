#ifndef ALARM_LED_TASK_H
#define ALARM_LED_TASK_H

#include <tk/tkernel.h>
#include "report_input.h"

/* Where the alarm LED gets the alarm and the window alarm. */
typedef struct {
	ReportInput *report_input;        /* the alarm */
	ReportInput *window_report_input; /* the window alarm */
	ID task_id;
} AlarmLedTask;

/*
 * Create the alarm LED at priority. The green LED blinks fast while only the alarm rings,
 * slowly while only the window alarm rings, stays on while both ring and is off otherwise.
 * Each alarm is shown for 2 s more after it ends.
 */
IMPORT ER alarm_led_task_create(AlarmLedTask *task, PRI priority, ReportInput *report_input,
	ReportInput *window_report_input);

/* Start the alarm LED. */
IMPORT ER alarm_led_task_start(AlarmLedTask *task);

#endif
