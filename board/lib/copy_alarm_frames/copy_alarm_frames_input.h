#ifndef COPY_ALARM_FRAMES_INPUT_H
#define COPY_ALARM_FRAMES_INPUT_H

#include <tk/tkernel.h>

/*
 * Where alarm A started, and the frame ring's positions of the frames behind the rows
 * that raised it.
 */
typedef struct {
	UW no;           /* the row alarm A started on */
	UW frames_start; /* the frame ring's place at the tick before the oldest of those rows */
	UW frames_end;   /* the frame ring's place at the tick of the row alarm A started on */
} AlarmFramePositions;

/*
 * The latest positions score and detect by row passes to the task that copies the alarm
 * frames, under a lock. New positions go over the ones before, so writing never waits
 * for the copy.
 */
typedef struct {
	ID mutex;            /* locks positions */
	ID wake_reader_flag; /* event flag that wakes the reader */
	AlarmFramePositions positions; /* the latest positions */
} CopyAlarmFramesInput;

/**
 * @brief Make the input, with no positions in it.
 *
 * @param[out] copy_alarm_frames_input The input.
 * @return E_OK, or the error T-Kernel gave while making its mutex or event flag.
 */
IMPORT ER copy_alarm_frames_input_create(CopyAlarmFramesInput *copy_alarm_frames_input);

/**
 * @brief Put positions over the ones before, and wake the reader.
 *
 * @param[in,out] copy_alarm_frames_input The input.
 * @param[in] positions The positions.
 */
IMPORT void copy_alarm_frames_input_write(CopyAlarmFramesInput *copy_alarm_frames_input,
	CONST AlarmFramePositions *positions);

/**
 * @brief Wait for a write, then copy the latest positions.
 *
 * @param[in,out] copy_alarm_frames_input The input.
 * @param[out] positions The latest positions.
 */
IMPORT void copy_alarm_frames_input_read(CopyAlarmFramesInput *copy_alarm_frames_input,
	AlarmFramePositions *positions);

#endif
