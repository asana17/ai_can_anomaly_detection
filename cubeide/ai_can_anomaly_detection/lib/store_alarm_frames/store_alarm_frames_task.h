#ifndef STORE_ALARM_FRAMES_TASK_H
#define STORE_ALARM_FRAMES_TASK_H

#include <tk/tkernel.h>
#include "alarm_frames_mac.h"
#include "flash_store.h"
#include "store_alarm_frames_input.h"
#include "stored_record_input.h"

/* Where the store gets the alarm frames and where it writes them. */
typedef struct {
	StoreAlarmFramesInput *store_alarm_frames_input; /* frames of the alarm by row */
	StoreAlarmFramesInput *store_window_alarm_frames_input; /* of the window alarm */
	FlashStoreState *flash_store; /* bank 2, made by flash_store_init */
	StoredRecordInput *stored_record_input; /* where each record of the alarm goes */
	StoredRecordInput *window_stored_record_input; /* of the window alarm */
	AlarmFramesRecord alarm_frames; /* the alarm frames being written, kept off the stack */
	AlarmFramesMac mac;             /* puts the MAC on them */
	ID task_id;
} StoreAlarmFramesTask;

/*
 * Create the store at priority. It puts a MAC on the alarm frames from
 * store_alarm_frames_input and writes them to flash_store. Each record written goes to
 * stored_record_input. The frames of the window alarm from
 * store_window_alarm_frames_input go the same way, and their records to
 * window_stored_record_input. It makes the MAC, so call it once.
 */
IMPORT ER store_alarm_frames_task_create(StoreAlarmFramesTask *task, PRI priority,
	StoreAlarmFramesInput *store_alarm_frames_input,
	StoreAlarmFramesInput *store_window_alarm_frames_input, FlashStoreState *flash_store,
	StoredRecordInput *stored_record_input,
	StoredRecordInput *window_stored_record_input);

/* Start the store. */
IMPORT ER store_alarm_frames_task_start(StoreAlarmFramesTask *task);

#endif
