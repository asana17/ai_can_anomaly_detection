#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "stm32h5xx_hal.h"
#include "slots.h"
#include "frame_ring.h"
#include "report_input.h"
#include "flash_store.h"
#include "store_alarm_frames_input.h"
#include "store_alarm_frames_task.h"
#include "stored_record_input.h"
#include "window_backlog_input.h"
#include "report_uart_task.h"
#include "stored_record_uart_task.h"
#include "window_backlog_uart_task.h"
#include "ai_can_anomaly_detection_tasks.h"
#include "replay_frames.h"

/* What the CAN receive side writes with slots_store(). */
EXPORT Slots slots;

/* The frames the replay copies for the cut. */
LOCAL FrameRing frame_ring;

LOCAL ReportInput report_input;
LOCAL ReportInput window_report_input;
LOCAL WindowBacklogInput window_backlog_input;
LOCAL StoredRecordInput stored_record_input;
LOCAL StoreAlarmFramesInput store_alarm_frames_input;
LOCAL FlashStoreState flash_store;
LOCAL StoreAlarmFramesTask store_alarm_frames_task;
LOCAL ReportUartTask report_uart_task;
LOCAL ReportUartTask window_report_uart_task;
LOCAL WindowBacklogUartTask window_backlog_uart_task;
LOCAL StoredRecordUartTask stored_record_uart_task;

/*
 * Store each Flash frame at its own time, as the CAN receive interrupt will. At the end,
 * print the fewest and most cycles one push into the frame ring took. An interrupt in a
 * push adds to its cycles.
 */
LOCAL void replay_task(INT stacd, void *exinf)
{
	SYSTIM start, now;
	UW i, due, elapsed, push_started, push_cycles;
	UW fewest_push_cycles = 0xFFFFFFFFu, most_push_cycles = 0;

	tk_get_otm(&start);
	for (i = 0; i < REPLAY_FRAMES; i++) {
		due = replay_frames[i].time_us / 1000u;
		tk_get_otm(&now);
		elapsed = now.lo - start.lo;
		if (due > elapsed) {
			tk_dly_tsk(due - elapsed);
		}
		slots_store(&slots, replay_frames[i].arb_id, replay_frames[i].data,
			replay_frames[i].size, replay_frames[i].time_us);
		/* DWT counts cycles once model_init has run, which is before the replay starts */
		push_started = DWT->CYCCNT;
		frame_ring_push(&frame_ring, replay_frames[i].arb_id, replay_frames[i].data,
			replay_frames[i].size, replay_frames[i].time_us);
		push_cycles = DWT->CYCCNT - push_started;
		if (push_cycles < fewest_push_cycles) {
			fewest_push_cycles = push_cycles;
		}
		if (push_cycles > most_push_cycles) {
			most_push_cycles = push_cycles;
		}
	}
	tm_printf((UB*)"frame ring push %u to %u cycles at %u Hz\n", fewest_push_cycles,
		most_push_cycles, SystemCoreClock);
	tk_ext_tsk();
}

LOCAL T_CTSK replay_ctsk = {
	.itskpri = 1, .stksz = 1024, .task = replay_task,
	.tskatr = TA_HLNG | TA_RNG3,
};

EXPORT INT usermain(void)
{
	ID replay;
	INT error;

	tm_printf((UB*)"replaying %d frames\n", REPLAY_FRAMES);
	frame_ring_clear(&frame_ring, 1u); /* the replay's times are in us */
	error = report_input_create(&report_input);
	if (error < E_OK) {
		return error;
	}
	error = report_input_create(&window_report_input);
	if (error < E_OK) {
		return error;
	}
	error = window_backlog_input_create(&window_backlog_input);
	if (error < E_OK) {
		return error;
	}
	error = stored_record_input_create(&stored_record_input);
	if (error < E_OK) {
		return error;
	}
	error = store_alarm_frames_input_create(&store_alarm_frames_input);
	if (error < E_OK) {
		return error;
	}
	error = flash_store_init(&flash_store);
	if (error < E_OK) {
		tm_printf((UB*)"flash store init error %d\n", error);
		return error;
	}
	/* above score and detect by window at 12, so the window model never holds back Flash */
	error = store_alarm_frames_task_create(&store_alarm_frames_task, 11,
		&store_alarm_frames_input, &flash_store, &stored_record_input);
	if (error < E_OK) {
		return error;
	}
	error = ai_can_anomaly_detection_tasks_create(&slots, &frame_ring, &report_input,
		&window_report_input, &window_backlog_input, &store_alarm_frames_input);
	if (error < E_OK) {
		return error;
	}
	/* between score and detect by row at 8 and the copy of the alarm frames at 10 */
	error = report_uart_task_create(&report_uart_task, 9, &report_input, ALARM_ID);
	if (error < E_OK) {
		return error;
	}
	/* above score and detect by window at 12, and below the alarm's report */
	error = report_uart_task_create(&window_report_uart_task, 10, &window_report_input,
		WINDOW_ALARM_ID);
	if (error < E_OK) {
		return error;
	}
	/* above score and detect by window at 12, so a backlog is printed while it lasts */
	error = window_backlog_uart_task_create(&window_backlog_uart_task, 10,
		&window_backlog_input, WINDOW_BACKLOG_ID);
	if (error < E_OK) {
		return error;
	}
	/* above the store at 11, so a record is printed as soon as it is written */
	error = stored_record_uart_task_create(&stored_record_uart_task, 10,
		&stored_record_input, STORED_RECORD_ID);
	if (error < E_OK) {
		return error;
	}
	replay = tk_cre_tsk(&replay_ctsk);
	if (replay < E_OK) {
		return replay;
	}
	error = report_uart_task_start(&report_uart_task);
	if (error < E_OK) {
		return error;
	}
	error = report_uart_task_start(&window_report_uart_task);
	if (error < E_OK) {
		return error;
	}
	error = window_backlog_uart_task_start(&window_backlog_uart_task);
	if (error < E_OK) {
		return error;
	}
	error = stored_record_uart_task_start(&stored_record_uart_task);
	if (error < E_OK) {
		return error;
	}
	error = store_alarm_frames_task_start(&store_alarm_frames_task);
	if (error < E_OK) {
		return error;
	}
	error = ai_can_anomaly_detection_tasks_start();
	if (error < E_OK) {
		return error;
	}
	tk_sta_tsk(replay, 0);
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
