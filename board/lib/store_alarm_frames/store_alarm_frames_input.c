#include <string.h>
#include <tk/tkernel.h>
#include "store_alarm_frames_input.h"

EXPORT ER store_alarm_frames_input_create(StoreAlarmFramesInput *store_alarm_frames_input)
{
	T_CMTX cmtx = {
		.mtxatr = TA_INHERIT,
	};
	T_CFLG cflg = {
		.flgatr = TA_TFIFO | TA_WSGL, .iflgptn = 0,
	};

	memset(&store_alarm_frames_input->alarm_frames, 0,
		sizeof(store_alarm_frames_input->alarm_frames));
	store_alarm_frames_input->mutex = tk_cre_mtx(&cmtx);
	if (store_alarm_frames_input->mutex < E_OK) {
		return store_alarm_frames_input->mutex;
	}
	store_alarm_frames_input->wake_reader_flag = tk_cre_flg(&cflg);
	if (store_alarm_frames_input->wake_reader_flag < E_OK) {
		return store_alarm_frames_input->wake_reader_flag;
	}
	return E_OK;
}

EXPORT void store_alarm_frames_input_write(StoreAlarmFramesInput *store_alarm_frames_input,
	CONST AlarmFramesRecord *alarm_frames)
{
	tk_loc_mtx(store_alarm_frames_input->mutex, TMO_FEVR);
	store_alarm_frames_input->alarm_frames = *alarm_frames;
	tk_unl_mtx(store_alarm_frames_input->mutex);
	tk_set_flg(store_alarm_frames_input->wake_reader_flag, 1);
}

EXPORT void store_alarm_frames_input_read(StoreAlarmFramesInput *store_alarm_frames_input,
	AlarmFramesRecord *alarm_frames)
{
	UINT pattern;

	tk_wai_flg(store_alarm_frames_input->wake_reader_flag, 1, TWF_ANDW | TWF_CLR, &pattern,
		TMO_FEVR);
	tk_loc_mtx(store_alarm_frames_input->mutex, TMO_FEVR);
	*alarm_frames = store_alarm_frames_input->alarm_frames;
	tk_unl_mtx(store_alarm_frames_input->mutex);
}
