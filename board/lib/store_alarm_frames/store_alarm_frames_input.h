#ifndef STORE_ALARM_FRAMES_INPUT_H
#define STORE_ALARM_FRAMES_INPUT_H

#include <tk/tkernel.h>
#include "alarm_frames_mac.h"
#include "alarm_kind.h"
#include "flash_store.h"
#include "frame_ring.h"

/* The frames a Flash store record holds after the head and the MAC */
#define ALARM_FRAMES_MAX \
	((FLASH_STORE_RECORD_MAX - FLASH_STORE_WORD - ALARM_FRAMES_MAC_BYTES) / \
		sizeof(FrameRingEntry))

/*
 * What is written to Flash for an alarm, a head of one Flash write, the MAC of two and
 * then the frames.
 */
typedef struct {
	UW no;          /* the row the alarm started on */
	UW frame_count; /* frames filled, from the first */
	UW alarm;       /* ALARM_KIND_ALARM or ALARM_KIND_WINDOW_ALARM */
	UW unused;      /* left 0, so the head fills one Flash write */
	UB mac[ALARM_FRAMES_MAC_BYTES]; /* HMAC-SHA256 of the head, then the frames filled */
	FrameRingEntry frames[ALARM_FRAMES_MAX]; /* oldest first */
} AlarmFramesRecord;

/*
 * The latest alarm frames of one alarm the task that copies them passes to the task that
 * stores them, under a lock. New alarm frames go over the ones before, so writing never
 * waits for the store. The input of the alarm by row and that of the window alarm share
 * the event flag that wakes the store, each with its own bit.
 */
typedef struct {
	ID mutex;             /* locks alarm_frames */
	ID wake_reader_flag;  /* event flag that wakes the reader, shared by both inputs */
	UINT wake_reader_bit; /* this input's bit in wake_reader_flag */
	AlarmFramesRecord alarm_frames; /* the latest alarm frames */
} StoreAlarmFramesInput;

/**
 * @brief Make the inputs of the alarm by row and of the window alarm, both empty.
 *
 * @param[out] alarm_input The input of the alarm by row.
 * @param[out] window_alarm_input The input of the window alarm.
 * @return E_OK, or the error T-Kernel gave while making a mutex or the event flag.
 */
IMPORT ER store_alarm_frames_input_create(StoreAlarmFramesInput *alarm_input,
	StoreAlarmFramesInput *window_alarm_input);

/**
 * @brief Put alarm frames over the ones before, and wake the reader.
 *
 * @param[in,out] store_alarm_frames_input The input.
 * @param[in] alarm_frames The alarm frames.
 */
IMPORT void store_alarm_frames_input_write(StoreAlarmFramesInput *store_alarm_frames_input,
	CONST AlarmFramesRecord *alarm_frames);

/**
 * @brief Wait for a write to either input, then copy the latest alarm frames of one. When
 *        both have alarm frames, those of the alarm by row are taken first. Given the
 *        same input twice, it waits on that input alone. Both inputs come from the same
 *        store_alarm_frames_input_create.
 *
 * @param[in,out] alarm_input The input of the alarm by row.
 * @param[in,out] window_alarm_input The input of the window alarm.
 * @param[out] alarm_frames The latest alarm frames of that input, left as they were on a
 *                          timeout.
 * @param[in] timeout The longest wait in ms, or TMO_FEVR.
 * @return E_OK, or E_TMOUT when no alarm frames came within timeout.
 */
IMPORT ER store_alarm_frames_input_read(StoreAlarmFramesInput *alarm_input,
	StoreAlarmFramesInput *window_alarm_input, AlarmFramesRecord *alarm_frames,
	TMO timeout);

#endif
