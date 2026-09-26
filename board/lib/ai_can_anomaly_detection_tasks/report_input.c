#include <tk/tkernel.h>
#include "mbf.h"
#include "report_input.h"

#define REPORTS_HELD 8

EXPORT ER report_input_create(ReportInput *report_input)
{
	T_CMBF cmbf = {
		.mbfatr = TA_TFIFO,
		.bufsz = REPORTS_HELD * MBF_MESSAGE_STORAGE_SIZE(sizeof(Report)),
		.maxmsz = sizeof(Report),
	};

	report_input->mbf = tk_cre_mbf(&cmbf);
	if (report_input->mbf < E_OK) {
		return report_input->mbf;
	}
	return E_OK;
}

EXPORT ER report_input_write(ReportInput *report_input, CONST Report *report)
{
	return tk_snd_mbf(report_input->mbf, (void *)report, sizeof(*report), TMO_FEVR);
}

EXPORT ER report_input_read(ReportInput *report_input, Report *report)
{
	INT size = tk_rcv_mbf(report_input->mbf, report, TMO_FEVR);

	if (size < E_OK) {
		return size;
	}
	return E_OK;
}
