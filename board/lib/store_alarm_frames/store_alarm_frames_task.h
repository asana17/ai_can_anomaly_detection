#ifndef STORE_ALARM_FRAMES_TASK_H
#define STORE_ALARM_FRAMES_TASK_H

#include <tk/tkernel.h>
#include "alarm_frames_mac.h"
#include "flash_store.h"
#include "store_alarm_frames_input.h"
#include "stored_record_input.h"

/* Where the store gets the alarm frames and where it writes them. */
typedef struct {
	StoreAlarmFramesInput *store_alarm_frames_input; /* where the alarm frames come from */
	FlashStoreState *flash_store;                    /* bank 2, made by flash_store_init */
	StoredRecordInput *stored_record_input;          /* where each record written goes */
	AlarmFramesRecord alarm_frames; /* the alarm frames being written, kept off the stack */
	AlarmFramesMac mac;             /* puts the MAC on them */
	ID task_id;
} StoreAlarmFramesTask;

/*
 * Create the store at priority. It puts a MAC on the alarm frames from
 * store_alarm_frames_input and writes them to flash_store. Each record written goes to
 * stored_record_input. It makes the MAC, so call it once.
 */
IMPORT ER store_alarm_frames_task_create(StoreAlarmFramesTask *task, PRI priority,
	StoreAlarmFramesInput *store_alarm_frames_input, FlashStoreState *flash_store,
	StoredRecordInput *stored_record_input);

/* Start the store. */
IMPORT ER store_alarm_frames_task_start(StoreAlarmFramesTask *task);

#endif
