#include <tk/tkernel.h>
#include "mbf.h"
#include "score_and_detect_by_row_input.h"

#define ROWS_HELD 4

EXPORT ER score_and_detect_by_row_input_create(
	ScoreAndDetectByRowInput *score_and_detect_by_row_input)
{
	T_CMBF cmbf = {
		.mbfatr = TA_TFIFO,
		.bufsz = ROWS_HELD * MBF_MESSAGE_STORAGE_SIZE(sizeof(Row)),
		.maxmsz = sizeof(Row),
	};

	score_and_detect_by_row_input->mbf = tk_cre_mbf(&cmbf);
	if (score_and_detect_by_row_input->mbf < E_OK) {
		return score_and_detect_by_row_input->mbf;
	}
	return E_OK;
}

EXPORT ER score_and_detect_by_row_input_write(
	ScoreAndDetectByRowInput *score_and_detect_by_row_input, CONST Row *row)
{
	Row dropped_row;
	INT dropped;

	return mbf_send_drop_oldest(score_and_detect_by_row_input->mbf, row, sizeof(*row),
		&dropped_row, &dropped);
}

EXPORT ER score_and_detect_by_row_input_read(
	ScoreAndDetectByRowInput *score_and_detect_by_row_input, Row *row)
{
	INT size = tk_rcv_mbf(score_and_detect_by_row_input->mbf, row, TMO_FEVR);

	if (size < E_OK) {
		return size;
	}
	return E_OK;
}
