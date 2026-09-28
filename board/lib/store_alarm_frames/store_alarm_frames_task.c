#include <stddef.h>
#include <tk/tkernel.h>
#include "store_alarm_frames_task.h"

/*
 * Put the MAC on each alarm frames record and write it to Flash. When no sector may be
 * erased yet, keep the record and write it once one may. Newer alarm frames that come
 * meanwhile take its place. A record whose MAC or write fails otherwise is dropped.
 */
LOCAL void store_alarm_frames_task(INT stacd, void *exinf)
{
	StoreAlarmFramesTask *task = exinf;
	TMO wait = TMO_FEVR; /* no record is held at first */
	UW size, sector;
	ER error;

	for (;;) {
		/* on a timeout the held record is written again */
		error = store_alarm_frames_input_read(task->store_alarm_frames_input,
			&task->alarm_frames, wait);
		if (error < E_OK && error != E_TMOUT) {
			break;
		}
		wait = TMO_FEVR;
		/* a held record has its MAC already */
		if (error == E_OK && alarm_frames_mac_compute(&task->mac, &task->alarm_frames,
			offsetof(AlarmFramesRecord, mac), task->alarm_frames.frames,
			task->alarm_frames.frame_count * (UW)sizeof(FrameRingEntry),
			task->alarm_frames.mac) < E_OK) {
			continue;
		}
		size = offsetof(AlarmFramesRecord, frames) +
			task->alarm_frames.frame_count * (UW)sizeof(FrameRingEntry);
		error = flash_store_write(task->flash_store, &task->alarm_frames, size, &sector);
		if (error == E_BUSY) {
			wait = (TMO)flash_store_ms_until_erase(task->flash_store);
		}
	}
	tk_ext_tsk();
}

EXPORT ER store_alarm_frames_task_create(StoreAlarmFramesTask *task, PRI priority,
	StoreAlarmFramesInput *store_alarm_frames_input, FlashStoreState *flash_store)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = store_alarm_frames_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};
	ER error;

	task->store_alarm_frames_input = store_alarm_frames_input;
	task->flash_store = flash_store;
	error = alarm_frames_mac_create(&task->mac);
	if (error < E_OK) {
		return error;
	}
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER store_alarm_frames_task_start(StoreAlarmFramesTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
