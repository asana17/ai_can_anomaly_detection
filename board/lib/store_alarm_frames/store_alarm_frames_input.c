#include <string.h>
#include <tk/tkernel.h>
#include "store_alarm_frames_input.h"

/* Make an input with no alarm frames in it, woken by bit of wake_reader_flag. */
LOCAL ER create_input(StoreAlarmFramesInput *store_alarm_frames_input,
	ID wake_reader_flag, UINT bit)
{
	T_CMTX cmtx = {
		.mtxatr = TA_INHERIT,
	};

	memset(&store_alarm_frames_input->alarm_frames, 0,
		sizeof(store_alarm_frames_input->alarm_frames));
	store_alarm_frames_input->wake_reader_flag = wake_reader_flag;
	store_alarm_frames_input->wake_reader_bit = bit;
	store_alarm_frames_input->mutex = tk_cre_mtx(&cmtx);
	if (store_alarm_frames_input->mutex < E_OK) {
		return store_alarm_frames_input->mutex;
	}
	return E_OK;
}

EXPORT ER store_alarm_frames_input_create(StoreAlarmFramesInput *alarm_input,
	StoreAlarmFramesInput *window_alarm_input)
{
	T_CFLG cflg = {
		.flgatr = TA_TFIFO | TA_WSGL, .iflgptn = 0,
	};
	ID wake_reader_flag;
	ER error;

	wake_reader_flag = tk_cre_flg(&cflg);
	if (wake_reader_flag < E_OK) {
		return wake_reader_flag;
	}
	error = create_input(alarm_input, wake_reader_flag, 1);
	if (error < E_OK) {
		return error;
	}
	return create_input(window_alarm_input, wake_reader_flag, 2);
}

EXPORT void store_alarm_frames_input_write(StoreAlarmFramesInput *store_alarm_frames_input,
	CONST AlarmFramesRecord *alarm_frames)
{
	tk_loc_mtx(store_alarm_frames_input->mutex, TMO_FEVR);
	store_alarm_frames_input->alarm_frames = *alarm_frames;
	tk_unl_mtx(store_alarm_frames_input->mutex);
	tk_set_flg(store_alarm_frames_input->wake_reader_flag,
		store_alarm_frames_input->wake_reader_bit);
}

EXPORT ER store_alarm_frames_input_read(StoreAlarmFramesInput *alarm_input,
	StoreAlarmFramesInput *window_alarm_input, AlarmFramesRecord *alarm_frames,
	TMO timeout)
{
	StoreAlarmFramesInput *input = window_alarm_input;
	UINT pattern;
	ER error;

	error = tk_wai_flg(alarm_input->wake_reader_flag,
		alarm_input->wake_reader_bit | window_alarm_input->wake_reader_bit, TWF_ORW,
		&pattern, timeout);
	if (error < E_OK) {
		return error;
	}
	if ((pattern & alarm_input->wake_reader_bit) != 0u) {
		input = alarm_input;
	}
	/* only the bit taken is cleared, so the other input's is read next */
	tk_clr_flg(input->wake_reader_flag, ~input->wake_reader_bit);
	tk_loc_mtx(input->mutex, TMO_FEVR);
	*alarm_frames = input->alarm_frames;
	tk_unl_mtx(input->mutex);
	return E_OK;
}
