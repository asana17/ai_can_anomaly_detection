#include <tk/tkernel.h>
#include "main.h"
#include "alarm_led_task.h"
#include "section_cycles.h"

#define STEP_MS 125     /* the fast blink's half period */
#define SLOW_STEPS 4u   /* steps in the slow blink's half period */
#define HOLD_MS 2000    /* how long an alarm stays shown after it ends */
#define HOLD_STEPS (HOLD_MS / STEP_MS)

/* Whether an alarm is shown this step. left counts down the steps after it ends. */
LOCAL BOOL shown(INT ringing, UW *left)
{
	if (ringing) {
		*left = HOLD_STEPS;
		return TRUE;
	}
	if (*left == 0u) {
		return FALSE;
	}
	(*left)--;
	return TRUE;
}

/* Whether the LED is lit at step for the alarm and the window alarm shown. */
LOCAL BOOL lit(INT alarm, INT window_alarm, UW step)
{
	if (alarm && window_alarm) {
		return TRUE;
	}
	if (alarm) {
		return (step % 2u) == 0u;
	}
	if (window_alarm) {
		return ((step / SLOW_STEPS) % 2u) == 0u;
	}
	return FALSE;
}

/* Show the alarm and the window alarm on the green LED. */
LOCAL void alarm_led_task(INT stacd, void *exinf)
{
	AlarmLedTask *task = exinf;
	Report report, window_report;
	UW step = 0, alarm_left = 0, window_alarm_left = 0, started;
	BOOL alarm, window_alarm;

	for (;;) {
		started = section_cycles_start();
		report_input_peek(task->report_input, &report);
		report_input_peek(task->window_report_input, &window_report);
		alarm = shown(report.alarm, &alarm_left);
		window_alarm = shown(window_report.alarm, &window_alarm_left);
		if (lit(alarm, window_alarm, step)) {
			BSP_LED_On(LED_GREEN);
		} else {
			BSP_LED_Off(LED_GREEN);
		}
		step++;
		section_cycles_end(SECTION_ALARM_LED, started);
		tk_dly_tsk(STEP_MS);
	}
}

EXPORT ER alarm_led_task_create(AlarmLedTask *task, PRI priority, ReportInput *report_input,
	ReportInput *window_report_input)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = alarm_led_task, .exinf = task,
		.tskatr = TA_HLNG | TA_RNG3,
	};

	task->report_input = report_input;
	task->window_report_input = window_report_input;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER alarm_led_task_start(AlarmLedTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
