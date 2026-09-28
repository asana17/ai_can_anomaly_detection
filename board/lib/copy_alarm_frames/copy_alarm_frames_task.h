#ifndef COPY_ALARM_FRAMES_TASK_H
#define COPY_ALARM_FRAMES_TASK_H

#include <tk/tkernel.h>
#include "copy_alarm_frames_input.h"
#include "frame_ring.h"
#include "store_alarm_frames_input.h"

/* Where the copy gets positions and frames, and where the alarm frames go. */
typedef struct {
	CopyAlarmFramesInput *copy_alarm_frames_input;   /* where the positions come from */
	FrameRing *frame_ring;                           /* the frames to copy from */
	StoreAlarmFramesInput *store_alarm_frames_input; /* where the alarm frames go */
	AlarmFramesRecord alarm_frames; /* the alarm frames being copied, kept off the stack */
	ID task_id;
} CopyAlarmFramesTask;

/*
 * Create the copy at priority. For the positions from copy_alarm_frames_input it copies
 * the frames from frame_ring and puts them in store_alarm_frames_input.
 */
IMPORT ER copy_alarm_frames_task_create(CopyAlarmFramesTask *task, PRI priority,
	CopyAlarmFramesInput *copy_alarm_frames_input, FrameRing *frame_ring,
	StoreAlarmFramesInput *store_alarm_frames_input);

/* Start the copy. */
IMPORT ER copy_alarm_frames_task_start(CopyAlarmFramesTask *task);

#endif
