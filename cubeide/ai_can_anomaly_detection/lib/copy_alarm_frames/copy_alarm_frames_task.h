#ifndef COPY_ALARM_FRAMES_TASK_H
#define COPY_ALARM_FRAMES_TASK_H

#include <tk/tkernel.h>
#include "copy_alarm_frames_input.h"
#include "frame_ring.h"
#include "store_alarm_frames_input.h"

/* Where the copy gets positions and frames, and where the alarm frames go. */
typedef struct {
	CopyAlarmFramesInput *copy_alarm_frames_input; /* positions of the alarm by row */
	CopyAlarmFramesInput *copy_window_alarm_frames_input; /* of the window alarm */
	FrameRing *frame_ring; /* the frames to copy from */
	StoreAlarmFramesInput *store_alarm_frames_input; /* where frames of the alarm go */
	StoreAlarmFramesInput *store_window_alarm_frames_input; /* of the window alarm */
	AlarmFramesRecord alarm_frames; /* the alarm frames being copied, kept off the stack */
	ID task_id;
} CopyAlarmFramesTask;

/*
 * Create the copy at priority. For the positions from copy_alarm_frames_input it copies
 * the frames from frame_ring and puts them in store_alarm_frames_input, and those of the
 * window alarm the same way.
 */
IMPORT ER copy_alarm_frames_task_create(CopyAlarmFramesTask *task, PRI priority,
	CopyAlarmFramesInput *copy_alarm_frames_input,
	CopyAlarmFramesInput *copy_window_alarm_frames_input, FrameRing *frame_ring,
	StoreAlarmFramesInput *store_alarm_frames_input,
	StoreAlarmFramesInput *store_window_alarm_frames_input);

/* Start the copy. */
IMPORT ER copy_alarm_frames_task_start(CopyAlarmFramesTask *task);

#endif
