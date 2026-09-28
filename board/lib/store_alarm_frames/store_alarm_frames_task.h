#ifndef STORE_ALARM_FRAMES_TASK_H
#define STORE_ALARM_FRAMES_TASK_H

#include <tk/tkernel.h>
#include "flash_store.h"
#include "store_alarm_frames_input.h"

/* Where the store gets the alarm frames and where it writes them. */
typedef struct {
	StoreAlarmFramesInput *store_alarm_frames_input; /* where the alarm frames come from */
	FlashStoreState *flash_store;                    /* bank 2, made by flash_store_init */
	AlarmFramesRecord alarm_frames; /* the alarm frames being written, kept off the stack */
	ID task_id;
} StoreAlarmFramesTask;

/*
 * Create the store at priority, writing the alarm frames from store_alarm_frames_input
 * to flash_store.
 */
IMPORT ER store_alarm_frames_task_create(StoreAlarmFramesTask *task, PRI priority,
	StoreAlarmFramesInput *store_alarm_frames_input, FlashStoreState *flash_store);

/* Start the store. */
IMPORT ER store_alarm_frames_task_start(StoreAlarmFramesTask *task);

#endif
