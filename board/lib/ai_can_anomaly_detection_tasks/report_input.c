#include <tk/tkernel.h>
#include "report_input.h"

EXPORT ER report_input_create(ReportInput *report_input)
{
	T_CMTX cmtx = {
		.mtxatr = TA_INHERIT,
	};
	T_CFLG cflg = {
		.flgatr = TA_TFIFO | TA_WSGL, .iflgptn = 0,
	};
	Report none = {0};

	report_input->report = none;
	report_input->mutex = tk_cre_mtx(&cmtx);
	if (report_input->mutex < E_OK) {
		return report_input->mutex;
	}
	report_input->wake_reader_flag = tk_cre_flg(&cflg);
	if (report_input->wake_reader_flag < E_OK) {
		return report_input->wake_reader_flag;
	}
	return E_OK;
}

EXPORT void report_input_write(ReportInput *report_input, CONST Report *report)
{
	tk_loc_mtx(report_input->mutex, TMO_FEVR);
	report_input->report = *report;
	tk_unl_mtx(report_input->mutex);
	tk_set_flg(report_input->wake_reader_flag, 1);
}

EXPORT void report_input_read(ReportInput *report_input, Report *report)
{
	UINT pattern;

	tk_wai_flg(report_input->wake_reader_flag, 1, TWF_ANDW | TWF_CLR, &pattern, TMO_FEVR);
	report_input_peek(report_input, report);
}

EXPORT void report_input_peek(ReportInput *report_input, Report *report)
{
	tk_loc_mtx(report_input->mutex, TMO_FEVR);
	*report = report_input->report;
	tk_unl_mtx(report_input->mutex);
}
