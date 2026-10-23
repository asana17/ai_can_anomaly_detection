#include <tk/tkernel.h>
#include "window_backlog_input.h"

EXPORT ER window_backlog_input_create(WindowBacklogInput *window_backlog_input)
{
	T_CMTX cmtx = {
		.mtxatr = TA_INHERIT,
	};
	T_CFLG cflg = {
		.flgatr = TA_TFIFO | TA_WSGL, .iflgptn = 0,
	};
	WindowBacklog none = {0};

	window_backlog_input->window_backlog = none;
	window_backlog_input->mutex = tk_cre_mtx(&cmtx);
	if (window_backlog_input->mutex < E_OK) {
		return window_backlog_input->mutex;
	}
	window_backlog_input->wake_reader_flag = tk_cre_flg(&cflg);
	if (window_backlog_input->wake_reader_flag < E_OK) {
		return window_backlog_input->wake_reader_flag;
	}
	return E_OK;
}

EXPORT void window_backlog_input_write(WindowBacklogInput *window_backlog_input,
	CONST WindowBacklog *window_backlog)
{
	tk_loc_mtx(window_backlog_input->mutex, TMO_FEVR);
	window_backlog_input->window_backlog = *window_backlog;
	tk_unl_mtx(window_backlog_input->mutex);
	tk_set_flg(window_backlog_input->wake_reader_flag, 1);
}

EXPORT void window_backlog_input_read(WindowBacklogInput *window_backlog_input,
	WindowBacklog *window_backlog)
{
	UINT pattern;

	tk_wai_flg(window_backlog_input->wake_reader_flag, 1, TWF_ANDW | TWF_CLR, &pattern,
		TMO_FEVR);
	tk_loc_mtx(window_backlog_input->mutex, TMO_FEVR);
	*window_backlog = window_backlog_input->window_backlog;
	tk_unl_mtx(window_backlog_input->mutex);
}
