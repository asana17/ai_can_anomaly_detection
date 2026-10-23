#ifndef WINDOW_BACKLOG_INPUT_H
#define WINDOW_BACKLOG_INPUT_H

#include <tk/tkernel.h>

/*
 * A row score and detect by window finished while the next row was already waiting, or
 * the first row after rows it lost.
 */
typedef struct {
	UW no;           /* the row's number */
	UW missing_rows; /* the rows lost just before it, overwritten before they were taken */
} WindowBacklog;

/*
 * The latest backlog score and detect by window passes to the task that reports it, under
 * a lock. A new backlog goes over the one before, so writing never waits for report.
 */
typedef struct {
	ID mutex;              /* locks window_backlog */
	ID wake_reader_flag;   /* event flag that wakes the reader */
	WindowBacklog window_backlog; /* the latest backlog */
} WindowBacklogInput;

/**
 * @brief Make the input, with no backlog in it.
 *
 * @param[out] window_backlog_input The input.
 * @return E_OK, or the error T-Kernel gave while making its mutex or event flag.
 */
IMPORT ER window_backlog_input_create(WindowBacklogInput *window_backlog_input);

/**
 * @brief Put a backlog over the one before, and wake the reader.
 *
 * @param[in,out] window_backlog_input The input.
 * @param[in] window_backlog The backlog.
 */
IMPORT void window_backlog_input_write(WindowBacklogInput *window_backlog_input,
	CONST WindowBacklog *window_backlog);

/**
 * @brief Wait for a write, then copy the latest backlog.
 *
 * @param[in,out] window_backlog_input The input.
 * @param[out] window_backlog The latest backlog.
 */
IMPORT void window_backlog_input_read(WindowBacklogInput *window_backlog_input,
	WindowBacklog *window_backlog);

#endif
