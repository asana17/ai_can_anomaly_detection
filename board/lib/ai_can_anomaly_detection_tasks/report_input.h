#ifndef REPORT_INPUT_H
#define REPORT_INPUT_H

#include <tk/tkernel.h>

/* The alarm state after its last start or end, for the task that reports it. */
typedef struct {
	UW no; /* the row of the last change */
	INT alarm; /* the alarm is ringing */
} Report;

/*
 * The latest report score and detect by row passes to the task that reports it, under a lock. A new report
 * goes over the one before, so writing never waits for report.
 */
typedef struct {
	ID mutex;            /* locks report */
	ID wake_reader_flag; /* event flag that wakes the reader */
	Report report;       /* the latest report */
} ReportInput;

/**
 * @brief Make the input, with the alarm not ringing.
 *
 * @param[out] report_input The input.
 * @return E_OK, or the error T-Kernel gave while making its mutex or event flag.
 */
IMPORT ER report_input_create(ReportInput *report_input);

/**
 * @brief Put a change over the report before, and wake the reader.
 *
 * @param[in,out] report_input The input.
 * @param[in] report The change.
 */
IMPORT void report_input_write(ReportInput *report_input, CONST Report *report);

/**
 * @brief Wait for a write, then copy the latest report.
 *
 * @param[in,out] report_input The input.
 * @param[out] report The latest report.
 */
IMPORT void report_input_read(ReportInput *report_input, Report *report);

#endif
