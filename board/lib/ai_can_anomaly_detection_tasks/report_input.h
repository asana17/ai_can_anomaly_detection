#ifndef REPORT_INPUT_H
#define REPORT_INPUT_H

#include <tk/tkernel.h>
#include "model.h"

/* An alarm starting or ending, or a scoring error, for report to print. */
typedef struct {
	UW no;
	UW score_bits; /* float32 score bits; avoids UART float formatting. */
	INT alarm; /* the row starts an alarm, or ends the one that was ringing */
	INT rule;
	ModelStatus error;
} Report;

/* The reports score and detect by row passes to report, in a message buffer. */
typedef struct {
	ID mbf;
} ReportInput;

/**
 * @brief Make the input, with no report in it.
 *
 * @param[out] report_input The input.
 * @return E_OK, or the error T-Kernel gave while making its message buffer.
 */
IMPORT ER report_input_create(ReportInput *report_input);

/**
 * @brief Add a report, waiting for room when the input is full.
 *
 * @param[in,out] report_input The input.
 * @param[in] report The report.
 * @return E_OK, or the error T-Kernel gave.
 */
IMPORT ER report_input_write(ReportInput *report_input, CONST Report *report);

/**
 * @brief Wait for a report and take it out.
 *
 * @param[in,out] report_input The input.
 * @param[out] report The report.
 * @return E_OK, or the error T-Kernel gave.
 */
IMPORT ER report_input_read(ReportInput *report_input, Report *report);

#endif
