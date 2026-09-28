#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "slots.h"
#include "frame_ring.h"
#include "report_input.h"
#include "report_uart_task.h"
#include "ai_can_anomaly_detection_tasks.h"
#include "replay_frames.h"

/* What the CAN receive side writes with slots_store(). */
EXPORT Slots slots;

/* The frames the replay copies for the cut. */
LOCAL FrameRing frame_ring;

LOCAL ReportInput report_input;
LOCAL ReportUartTask report_uart_task;

/* Store each Flash frame at its own time, as the CAN receive interrupt will. */
LOCAL void replay_task(INT stacd, void *exinf)
{
	SYSTIM start, now;
	UW i, due, elapsed;

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
		frame_ring_push(&frame_ring, replay_frames[i].arb_id, replay_frames[i].data,
			replay_frames[i].size, replay_frames[i].time_us);
	}
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
	error = ai_can_anomaly_detection_tasks_create(&slots, &report_input);
	if (error < E_OK) {
		return error;
	}
	/* below score and detect by row at 8, above the windowed model at 11 */
	error = report_uart_task_create(&report_uart_task, 10, &report_input);
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
	error = ai_can_anomaly_detection_tasks_start();
	if (error < E_OK) {
		return error;
	}
	tk_sta_tsk(replay, 0);
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
