#ifndef COPY_ALARM_FRAMES_INPUT_H
#define COPY_ALARM_FRAMES_INPUT_H

#include <tk/tkernel.h>
#include "alarm_kind.h"

/*
 * Where an alarm started, and the frame ring's positions of the frames behind the rows
 * that raised it.
 */
typedef struct {
	UW alarm;        /* ALARM_KIND_ALARM or ALARM_KIND_WINDOW_ALARM */
	UW no;           /* the row the alarm started on */
	UW frames_start; /* the frame ring's place at the tick before the oldest of those rows */
	UW frames_end;   /* the frame ring's place at the tick of the row no */
} AlarmFramePositions;

/*
 * The latest positions of one alarm, passed to the task that copies the alarm frames,
 * under a lock. New positions go over the ones before, so writing never waits for the
 * copy. The input of the alarm by row and that of the window alarm share the event flag
 * that wakes the copy, each with its own bit.
 */
typedef struct {
	ID mutex;             /* locks positions */
	ID wake_reader_flag;  /* event flag that wakes the reader, shared by both inputs */
	UINT wake_reader_bit; /* this input's bit in wake_reader_flag */
	AlarmFramePositions positions; /* the latest positions */
} CopyAlarmFramesInput;

/**
 * @brief Make the inputs of the alarm by row and of the window alarm, both empty.
 *
 * @param[out] alarm_input The input of the alarm by row.
 * @param[out] window_alarm_input The input of the window alarm.
 * @return E_OK, or the error T-Kernel gave while making a mutex or the event flag.
 */
IMPORT ER copy_alarm_frames_input_create(CopyAlarmFramesInput *alarm_input,
	CopyAlarmFramesInput *window_alarm_input);

/**
 * @brief Put positions over the ones before, and wake the reader.
 *
 * @param[in,out] copy_alarm_frames_input The input.
 * @param[in] positions The positions.
 */
IMPORT void copy_alarm_frames_input_write(CopyAlarmFramesInput *copy_alarm_frames_input,
	CONST AlarmFramePositions *positions);

/**
 * @brief Wait for a write to either input, then copy the latest positions of one. When
 *        both have positions, those of the alarm by row are taken first. Both inputs
 *        come from the same copy_alarm_frames_input_create.
 *
 * @param[in,out] alarm_input The input of the alarm by row.
 * @param[in,out] window_alarm_input The input of the window alarm.
 * @param[out] positions The latest positions of that input.
 */
IMPORT void copy_alarm_frames_input_read(CopyAlarmFramesInput *alarm_input,
	CopyAlarmFramesInput *window_alarm_input, AlarmFramePositions *positions);

#endif
