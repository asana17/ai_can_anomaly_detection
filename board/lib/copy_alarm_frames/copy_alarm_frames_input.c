#include <tk/tkernel.h>
#include "copy_alarm_frames_input.h"

/* Make an input with no positions in it, woken by bit of wake_reader_flag. */
LOCAL ER create_input(CopyAlarmFramesInput *copy_alarm_frames_input, ID wake_reader_flag,
	UINT bit)
{
	T_CMTX cmtx = {
		.mtxatr = TA_INHERIT,
	};
	AlarmFramePositions none = {0};

	copy_alarm_frames_input->positions = none;
	copy_alarm_frames_input->wake_reader_flag = wake_reader_flag;
	copy_alarm_frames_input->wake_reader_bit = bit;
	copy_alarm_frames_input->mutex = tk_cre_mtx(&cmtx);
	if (copy_alarm_frames_input->mutex < E_OK) {
		return copy_alarm_frames_input->mutex;
	}
	return E_OK;
}

EXPORT ER copy_alarm_frames_input_create(CopyAlarmFramesInput *alarm_input,
	CopyAlarmFramesInput *window_alarm_input)
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

EXPORT void copy_alarm_frames_input_write(CopyAlarmFramesInput *copy_alarm_frames_input,
	CONST AlarmFramePositions *positions)
{
	tk_loc_mtx(copy_alarm_frames_input->mutex, TMO_FEVR);
	copy_alarm_frames_input->positions = *positions;
	tk_unl_mtx(copy_alarm_frames_input->mutex);
	tk_set_flg(copy_alarm_frames_input->wake_reader_flag,
		copy_alarm_frames_input->wake_reader_bit);
}

EXPORT void copy_alarm_frames_input_read(CopyAlarmFramesInput *alarm_input,
	CopyAlarmFramesInput *window_alarm_input, AlarmFramePositions *positions)
{
	CopyAlarmFramesInput *input = window_alarm_input;
	UINT pattern;

	tk_wai_flg(alarm_input->wake_reader_flag,
		alarm_input->wake_reader_bit | window_alarm_input->wake_reader_bit, TWF_ORW,
		&pattern, TMO_FEVR);
	if ((pattern & alarm_input->wake_reader_bit) != 0u) {
		input = alarm_input;
	}
	/* only the bit taken is cleared, so the other input's is read next */
	tk_clr_flg(input->wake_reader_flag, ~input->wake_reader_bit);
	tk_loc_mtx(input->mutex, TMO_FEVR);
	*positions = input->positions;
	tk_unl_mtx(input->mutex);
}
