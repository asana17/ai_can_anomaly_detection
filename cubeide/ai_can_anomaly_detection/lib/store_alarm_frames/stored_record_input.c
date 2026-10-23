#include <tk/tkernel.h>
#include "stored_record_input.h"

EXPORT ER stored_record_input_create(StoredRecordInput *stored_record_input)
{
	T_CMTX cmtx = {
		.mtxatr = TA_INHERIT,
	};
	T_CFLG cflg = {
		.flgatr = TA_TFIFO | TA_WSGL, .iflgptn = 0,
	};
	StoredRecord none = {0};

	stored_record_input->stored_record = none;
	stored_record_input->mutex = tk_cre_mtx(&cmtx);
	if (stored_record_input->mutex < E_OK) {
		return stored_record_input->mutex;
	}
	stored_record_input->wake_reader_flag = tk_cre_flg(&cflg);
	if (stored_record_input->wake_reader_flag < E_OK) {
		return stored_record_input->wake_reader_flag;
	}
	return E_OK;
}

EXPORT void stored_record_input_write(StoredRecordInput *stored_record_input,
	CONST StoredRecord *stored_record)
{
	tk_loc_mtx(stored_record_input->mutex, TMO_FEVR);
	stored_record_input->stored_record = *stored_record;
	tk_unl_mtx(stored_record_input->mutex);
	tk_set_flg(stored_record_input->wake_reader_flag, 1);
}

EXPORT void stored_record_input_read(StoredRecordInput *stored_record_input,
	StoredRecord *stored_record)
{
	UINT pattern;

	tk_wai_flg(stored_record_input->wake_reader_flag, 1, TWF_ANDW | TWF_CLR, &pattern,
		TMO_FEVR);
	tk_loc_mtx(stored_record_input->mutex, TMO_FEVR);
	*stored_record = stored_record_input->stored_record;
	tk_unl_mtx(stored_record_input->mutex);
}
