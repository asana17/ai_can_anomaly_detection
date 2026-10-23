#include <tk/tkernel.h>
#include "copy_alarm_frames_task.h"
#include "section_cycles.h"

/*
 * Copy the frames from start to end, the latest ALARM_FRAMES_MAX of them, oldest first.
 * The ring is read without stopping interrupts. When newer frames went over any of them
 * before the copy ended, none is kept.
 */
LOCAL void copy_frames(CONST FrameRing *ring, UW start, UW end,
	AlarmFramesRecord *alarm_frames)
{
	UW count, i;

	if (end - start > ALARM_FRAMES_MAX) {
		start = end - ALARM_FRAMES_MAX;
	}
	count = end - start;
	for (i = 0; i < count; i++) {
		alarm_frames->frames[i] = *frame_ring_entry(ring, start + i);
	}
	if (ring->position - start > FRAME_RING_FRAMES) {
		count = 0;
	}
	alarm_frames->frame_count = count;
}

/*
 * For each alarm start, copy the frames behind it and hand them on.
 */
LOCAL void copy_alarm_frames_task(INT stacd, void *exinf)
{
	CopyAlarmFramesTask *task = exinf;
	AlarmFramePositions positions;
	StoreAlarmFramesInput *store_input;
	UW started;

	for (;;) {
		copy_alarm_frames_input_read(task->copy_alarm_frames_input,
			task->copy_window_alarm_frames_input, &positions);
		started = section_cycles_start();
		task->alarm_frames.no = positions.no;
		task->alarm_frames.alarm = positions.alarm;
		copy_frames(task->frame_ring, positions.frames_start, positions.frames_end,
			&task->alarm_frames);
		store_input = task->store_alarm_frames_input;
		if (positions.alarm == ALARM_KIND_WINDOW_ALARM) {
			store_input = task->store_window_alarm_frames_input;
		}
		store_alarm_frames_input_write(store_input, &task->alarm_frames);
		section_cycles_end(SECTION_COPY_ALARM_FRAMES, started);
	}
}

EXPORT ER copy_alarm_frames_task_create(CopyAlarmFramesTask *task, PRI priority,
	CopyAlarmFramesInput *copy_alarm_frames_input,
	CopyAlarmFramesInput *copy_window_alarm_frames_input, FrameRing *frame_ring,
	StoreAlarmFramesInput *store_alarm_frames_input,
	StoreAlarmFramesInput *store_window_alarm_frames_input)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = copy_alarm_frames_task,
		.exinf = task, .tskatr = TA_HLNG | TA_RNG3,
	};

	task->copy_alarm_frames_input = copy_alarm_frames_input;
	task->copy_window_alarm_frames_input = copy_window_alarm_frames_input;
	task->frame_ring = frame_ring;
	task->store_alarm_frames_input = store_alarm_frames_input;
	task->store_window_alarm_frames_input = store_window_alarm_frames_input;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER copy_alarm_frames_task_start(CopyAlarmFramesTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
