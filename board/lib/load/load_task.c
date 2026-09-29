#include <tk/tkernel.h>
#include "load_task.h"

#define LOAD_BYTES 64u         /* bytes one work unit runs the CRC over */
#define CRC32_POLY 0xEDB88320u /* CRC-32, reflected */

LOCAL UB load_bytes[LOAD_BYTES];
LOCAL volatile UW load_crc; /* keeps the compiler from dropping the work */

EXPORT void load_work(UW units)
{
	UW unit, i, bit, crc;

	for (unit = 0; unit < units; unit++) {
		crc = 0xFFFFFFFFu;
		for (i = 0; i < LOAD_BYTES; i++) {
			crc ^= load_bytes[i];
			for (bit = 0; bit < 8u; bit++) {
				if (crc & 1u) {
					crc = (crc >> 1) ^ CRC32_POLY;
				} else {
					crc >>= 1;
				}
			}
		}
		load_crc = ~crc;
	}
}

LOCAL void load_tick(void *exinf)
{
	tk_wup_tsk(((LoadTask *)exinf)->task_id);
}

/* On each tick, do the work. */
LOCAL void load_task(INT stacd, void *exinf)
{
	LoadTask *task = exinf;

	while (tk_slp_tsk(TMO_FEVR) == E_OK) {
		load_work(task->units);
	}
	tk_ext_tsk();
}

EXPORT ER load_task_create(LoadTask *task, PRI priority, RELTIM period, UW units)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 512, .task = load_task, .exinf = task,
		.tskatr = TA_HLNG | TA_RNG3,
	};
	T_CCYC ccyc = {
		.cycatr = TA_HLNG, .cychdr = (FP)load_tick, .exinf = task,
		.cyctim = period, .cycphs = period,
	};

	task->units = units;
	task->task_id = tk_cre_tsk(&ctsk);
	if (task->task_id < E_OK) {
		return task->task_id;
	}
	task->tick_id = tk_cre_cyc(&ccyc);
	if (task->tick_id < E_OK) {
		return task->tick_id;
	}
	return E_OK;
}

EXPORT ER load_task_start(LoadTask *task)
{
	ER error;

	error = tk_sta_tsk(task->task_id, 0);
	if (error < E_OK) {
		return error;
	}
	return tk_sta_cyc(task->tick_id);
}
