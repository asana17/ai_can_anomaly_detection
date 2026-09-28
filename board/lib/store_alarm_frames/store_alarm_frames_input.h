#ifndef STORE_ALARM_FRAMES_INPUT_H
#define STORE_ALARM_FRAMES_INPUT_H

#include <tk/tkernel.h>
#include "flash_store.h"
#include "frame_ring.h"

/* The frames a Flash store record holds after the head */
#define ALARM_FRAMES_MAX \
	((FLASH_STORE_RECORD_MAX - FLASH_STORE_WORD) / sizeof(FrameRingEntry))

/* What is written to Flash for an alarm, a head of one Flash write and then the frames. */
typedef struct {
	UW no;          /* the row alarm A started on */
	UW frame_count; /* frames filled, from the first */
	UW unused[2];   /* left 0, so the head fills one Flash write */
	FrameRingEntry frames[ALARM_FRAMES_MAX]; /* oldest first */
} AlarmFramesRecord;

/*
 * The latest alarm frames the task that copies them passes to the task that stores
 * them, under a lock. New alarm frames go over the ones before, so writing never waits
 * for the store.
 */
typedef struct {
	ID mutex;                       /* locks alarm_frames */
	ID wake_reader_flag;            /* event flag that wakes the reader */
	AlarmFramesRecord alarm_frames; /* the latest alarm frames */
} StoreAlarmFramesInput;

/**
 * @brief Make the input, with no alarm frames in it.
 *
 * @param[out] store_alarm_frames_input The input.
 * @return E_OK, or the error T-Kernel gave while making its mutex or event flag.
 */
IMPORT ER store_alarm_frames_input_create(StoreAlarmFramesInput *store_alarm_frames_input);

/**
 * @brief Put alarm frames over the ones before, and wake the reader.
 *
 * @param[in,out] store_alarm_frames_input The input.
 * @param[in] alarm_frames The alarm frames.
 */
IMPORT void store_alarm_frames_input_write(StoreAlarmFramesInput *store_alarm_frames_input,
	CONST AlarmFramesRecord *alarm_frames);

/**
 * @brief Wait for a write, then copy the latest alarm frames.
 *
 * @param[in,out] store_alarm_frames_input The input.
 * @param[out] alarm_frames The latest alarm frames.
 */
IMPORT void store_alarm_frames_input_read(StoreAlarmFramesInput *store_alarm_frames_input,
	AlarmFramesRecord *alarm_frames);

#endif
