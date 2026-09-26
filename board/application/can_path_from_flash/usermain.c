#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "slots.h"
#include "ai_can_anomaly_detection_tasks.h"
#include "replay_frames.h"

/* What the CAN receive side writes with slots_store(). */
EXPORT Slots slots;

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
	error = ai_can_anomaly_detection_tasks_create(&slots);
	if (error < E_OK) {
		return error;
	}
	replay = tk_cre_tsk(&replay_ctsk);
	if (replay < E_OK) {
		return replay;
	}
	error = ai_can_anomaly_detection_tasks_start();
	if (error < E_OK) {
		return error;
	}
	tk_sta_tsk(replay, 0);
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
