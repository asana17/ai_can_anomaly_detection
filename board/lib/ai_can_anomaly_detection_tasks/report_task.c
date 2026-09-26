#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "detect_instant.h"
#include "report_task.h"
#include "ai_can_anomaly_detection_tasks.h"

/* Print alarms over UART, and what the tasks counted at the end. */
LOCAL void report_task(INT stacd, void *exinf)
{
	ReportTask *task = exinf;
	CONST TaskCounts *counts = task->counts;
	Report report;
	INT alarms = 0, errors = 0;

	tm_printf((UB*)"%s: k %u of %u\n", task->model_id, ALARM_K, DETECT_INSTANT_ROWS);
	while(tk_rcv_mbf(task->report_mbf, &report, TMO_FEVR) == sizeof(report)) {
		if(report.no == END_ROW) {
			break;
		}
		if(report.error != MODEL_OK) {
			errors++;
			tm_printf((UB*)"row %u error %d\n", report.no, report.error);
			continue;
		}
		alarms += report.alarm;
		if(report.alarm) {
			tm_printf((UB*)"alarm start at row %u score 0x%08x rule %d\n",
				report.no, report.score_bits, report.rule);
		} else {
			tm_printf((UB*)"alarm end at row %u score 0x%08x rule %d\n",
				report.no, report.score_bits, report.rule);
		}
	}
	tm_printf((UB*)"frames %u, resets %u, rows sent %u, quiet %u,"
		" not ready %u, skipped %u, dropped %u\n", task->slots->frames,
		counts->resets, counts->rows_sent, counts->rows_quiet,
		counts->rows_not_ready, counts->rows_skipped, counts->rows_dropped);
	tm_printf((UB*)"scored %u, flagged_rows %u, alarms %d, errors %d,"
		" max_cycles %u\n", counts->scored_rows,
		counts->flagged_rows, alarms, errors,
		counts->maximum_cycles);
	tk_slp_tsk(TMO_FEVR);
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
