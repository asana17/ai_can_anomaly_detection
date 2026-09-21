#include <string.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "mbf.h"
#include "raw_rows.h"

#define ROW_DEPTH 4
#define REPORT_DEPTH 8
#define PROGRESS_EVERY (RULE_ROWS < 20 ? 1 : 20)

typedef struct {
	UW no;
	float physical[RULE_SIGNALS];
} Row;

typedef struct {
	UW no;
	INT hit;
} Report;

LOCAL ID row_mbf, report_mbf;
LOCAL volatile INT source_dropped;

LOCAL T_CMBF row_cmbf = {
	.mbfatr = TA_TFIFO,
	.bufsz = ROW_DEPTH * MBF_MESSAGE_STORAGE_SIZE(sizeof(Row)),
	.maxmsz = sizeof(Row),
};
LOCAL T_CMBF report_cmbf = {
	.mbfatr = TA_TFIFO,
	.bufsz = REPORT_DEPTH * MBF_MESSAGE_STORAGE_SIZE(sizeof(Report)),
	.maxmsz = sizeof(Report),
};

/* Send one Flash row every 100 ms. */
LOCAL void source_task(INT stacd, void *exinf)
{
	Row row = {0}, old;
	INT dropped;
	UW i;

	for(i = 0; i < RULE_ROWS; i++) {
		row.no = i;
		memcpy(row.physical, physical_rows[i], sizeof(row.physical));
		if(mbf_send_drop_oldest(row_mbf, &row, sizeof(row), &old, &dropped) != E_OK) {
			break;
		}
		source_dropped += dropped;
		tk_dly_tsk(100);
	}
	row.no = RULE_ROWS;
	/* Wait for space so the end marker does not drop a row. */
	tk_snd_mbf(row_mbf, &row, sizeof(row), TMO_FEVR);
	tk_slp_tsk(TMO_FEVR);
}

LOCAL INT reverse_speed_rule(const Row *row)
{
	const float wheel = row->physical[WHEEL_SPEED_INDEX];
	const float gear = row->physical[CURRENT_GEAR_INDEX];

	return gear < 0.0f && wheel > 10.0f;
}

/* Run the rule on each row and send the result to the report task. */
LOCAL void rules_task(INT stacd, void *exinf)
{
	Row row;
	Report report = {0};

	while(tk_rcv_mbf(row_mbf, &row, TMO_FEVR) == sizeof(row)) {
		if(row.no == RULE_ROWS) {
			break;
		}
		report.no = row.no;
		report.hit = reverse_speed_rule(&row);
		tk_snd_mbf(report_mbf, &report, sizeof(report), TMO_FEVR);
	}
	report.no = RULE_ROWS;
	tk_snd_mbf(report_mbf, &report, sizeof(report), TMO_FEVR);
	tk_slp_tsk(TMO_FEVR);
}

/* Print progress and rule hits over UART. */
LOCAL void report_task(INT stacd, void *exinf)
{
	Report report;
	INT flagged_rows = 0, processed = 0;

	tm_printf((UB*)"reverse rule: starting %d rows at row %d\n", RULE_ROWS, FIRST_ROW);

	while(tk_rcv_mbf(report_mbf, &report, TMO_FEVR) == sizeof(report)) {
		if(report.no == RULE_ROWS) {
			break;
		}
		processed++;
		flagged_rows += report.hit;
		if(processed % PROGRESS_EVERY == 0) {
			tm_printf((UB*)"progress %d/%d at row %d, flagged_rows %d\n",
				processed, RULE_ROWS, FIRST_ROW + report.no, flagged_rows);
		}
	}
	tm_printf((UB*)"reverse rule: processed %d/%d, flagged_rows %d, dropped %d\n",
		processed, RULE_ROWS, flagged_rows, source_dropped);
	tk_slp_tsk(TMO_FEVR);
}

LOCAL T_CTSK source_ctsk = {
	.itskpri = 6, .stksz = 1024, .task = source_task,
	.tskatr = TA_HLNG | TA_RNG3,
};
LOCAL T_CTSK rules_ctsk = {
	.itskpri = 8, .stksz = 1024, .task = rules_task,
	.tskatr = TA_HLNG | TA_RNG3,
};
LOCAL T_CTSK report_ctsk = {
	.itskpri = 5, .stksz = 1024, .task = report_task,
	.tskatr = TA_HLNG | TA_RNG3,
};

EXPORT INT usermain(void)
{
	ID source, rules, report;

	row_mbf = tk_cre_mbf(&row_cmbf);
	report_mbf = tk_cre_mbf(&report_cmbf);
	if(row_mbf < E_OK || report_mbf < E_OK) {
		return -1;
	}
	source = tk_cre_tsk(&source_ctsk);
	rules = tk_cre_tsk(&rules_ctsk);
	report = tk_cre_tsk(&report_ctsk);
	if(source < E_OK || rules < E_OK || report < E_OK) {
		return -1;
	}
	tk_sta_tsk(report, 0);
	tk_sta_tsk(rules, 0);
	tk_sta_tsk(source, 0);
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
