#include <tk/tkernel.h>
#include "score_and_detect_by_window_input.h"

EXPORT ER score_and_detect_by_window_input_create(ScoreAndDetectByWindowInput *score_and_detect_by_window_input)
{
	T_CMTX cmtx = {
		.mtxatr = TA_INHERIT,
	};
	T_CFLG cflg = {
		.flgatr = TA_TFIFO | TA_WSGL, .iflgptn = 0,
	};

	row_ring_clear(&score_and_detect_by_window_input->row_ring);
	score_and_detect_by_window_input->mutex = tk_cre_mtx(&cmtx);
	if (score_and_detect_by_window_input->mutex < E_OK) {
		return score_and_detect_by_window_input->mutex;
	}
	score_and_detect_by_window_input->wake_reader_flag = tk_cre_flg(&cflg);
	if (score_and_detect_by_window_input->wake_reader_flag < E_OK) {
		return score_and_detect_by_window_input->wake_reader_flag;
	}
	return E_OK;
}

EXPORT void score_and_detect_by_window_input_write(ScoreAndDetectByWindowInput *score_and_detect_by_window_input,
	CONST RowRingEntry *entry)
{
	tk_loc_mtx(score_and_detect_by_window_input->mutex, TMO_FEVR);
	row_ring_push(&score_and_detect_by_window_input->row_ring, entry);
	tk_unl_mtx(score_and_detect_by_window_input->mutex);
	tk_set_flg(score_and_detect_by_window_input->wake_reader_flag, 1);
}

EXPORT void score_and_detect_by_window_input_read(ScoreAndDetectByWindowInput *score_and_detect_by_window_input,
	RowRing *dest_row_ring)
{
	UINT pattern;

	tk_wai_flg(score_and_detect_by_window_input->wake_reader_flag, 1, TWF_ANDW | TWF_CLR, &pattern,
		TMO_FEVR);
	tk_loc_mtx(score_and_detect_by_window_input->mutex, TMO_FEVR);
	*dest_row_ring = score_and_detect_by_window_input->row_ring;
	row_ring_clear(&score_and_detect_by_window_input->row_ring);
	tk_unl_mtx(score_and_detect_by_window_input->mutex);
}
