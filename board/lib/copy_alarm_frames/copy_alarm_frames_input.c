#include <tk/tkernel.h>
#include "copy_alarm_frames_input.h"

EXPORT ER copy_alarm_frames_input_create(CopyAlarmFramesInput *copy_alarm_frames_input)
{
	T_CMTX cmtx = {
		.mtxatr = TA_INHERIT,
	};
	T_CFLG cflg = {
		.flgatr = TA_TFIFO | TA_WSGL, .iflgptn = 0,
	};
	AlarmFramePositions none = {0};

	copy_alarm_frames_input->positions = none;
	copy_alarm_frames_input->mutex = tk_cre_mtx(&cmtx);
	if (copy_alarm_frames_input->mutex < E_OK) {
		return copy_alarm_frames_input->mutex;
	}
	copy_alarm_frames_input->wake_reader_flag = tk_cre_flg(&cflg);
	if (copy_alarm_frames_input->wake_reader_flag < E_OK) {
		return copy_alarm_frames_input->wake_reader_flag;
	}
	return E_OK;
}

EXPORT void copy_alarm_frames_input_write(CopyAlarmFramesInput *copy_alarm_frames_input,
	CONST AlarmFramePositions *positions)
{
	tk_loc_mtx(copy_alarm_frames_input->mutex, TMO_FEVR);
	copy_alarm_frames_input->positions = *positions;
	tk_unl_mtx(copy_alarm_frames_input->mutex);
	tk_set_flg(copy_alarm_frames_input->wake_reader_flag, 1);
}

EXPORT void copy_alarm_frames_input_read(CopyAlarmFramesInput *copy_alarm_frames_input,
	AlarmFramePositions *positions)
{
	UINT pattern;

	tk_wai_flg(copy_alarm_frames_input->wake_reader_flag, 1, TWF_ANDW | TWF_CLR, &pattern,
		TMO_FEVR);
	tk_loc_mtx(copy_alarm_frames_input->mutex, TMO_FEVR);
	*positions = copy_alarm_frames_input->positions;
	tk_unl_mtx(copy_alarm_frames_input->mutex);
}
