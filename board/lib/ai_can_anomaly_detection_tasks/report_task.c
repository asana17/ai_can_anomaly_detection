#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "detect_instant.h"
#include "report_task.h"
#include "ai_can_anomaly_detection_tasks.h"

/* Print each alarm over UART. */
LOCAL void report_task(INT stacd, void *exinf)
{
	ReportTask *task = exinf;
	Report report;

	tm_printf((UB*)"%s: k %u of %u\n", task->model_id, ALARM_K, DETECT_INSTANT_ROWS);
	while(tk_rcv_mbf(task->report_mbf, &report, TMO_FEVR) == sizeof(report)) {
		if(report.error != MODEL_OK) {
			tm_printf((UB*)"row %u error %d\n", report.no, report.error);
			continue;
		}
		if(report.alarm) {
			tm_printf((UB*)"alarm start at row %u score 0x%08x rule %d\n",
				report.no, report.score_bits, report.rule);
		} else {
			tm_printf((UB*)"alarm end at row %u score 0x%08x rule %d\n",
				report.no, report.score_bits, report.rule);
		}
	}
	tk_ext_tsk();
}

EXPORT ER report_task_create(ReportTask *task, PRI priority, ID report_mbf)
{
	T_CTSK ctsk = {
		.itskpri = priority, .stksz = 1024, .task = report_task, .exinf = task,
		.tskatr = TA_HLNG | TA_RNG3,
	};

	task->report_mbf = report_mbf;
	task->task_id = tk_cre_tsk(&ctsk);
	return task->task_id;
}

EXPORT ER report_task_start(ReportTask *task)
{
	return tk_sta_tsk(task->task_id, 0);
}
