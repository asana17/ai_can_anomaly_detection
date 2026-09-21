#include <string.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "mbf.h"
#include "model.h"
#include "scale.h"
#include "scoring_error.h"
#include "model_config.h"
#include "threshold.h"
#include "../rule_check_from_flash/raw_rows.h"

#if RULE_SIGNALS != MODEL_SIGNALS
#error "Flash rows and the selected model use different signal counts"
#endif

#define ROW_DEPTH 4
#define REPORT_DEPTH 8
#define PROGRESS_EVERY (RULE_ROWS < 20 ? 1 : 20)

typedef struct {
	UW no;
	float physical[RULE_SIGNALS];
} Row;

typedef struct {
	UW no;
	UW score_bits; /* float32 MSE bits; avoids UART float formatting. */
	UW cycles;
	INT flagged;
	ModelStatus error;
} Report;

typedef struct {
	float score;
	UW cycles;
	INT flagged;
} Scored;

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

/* Send one physical row from Flash every 100 ms. */
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
	tk_snd_mbf(row_mbf, &row, sizeof(row), TMO_FEVR);
	tk_slp_tsk(TMO_FEVR);
}

/* Score a row with the autoencoder alone and compare the score with the threshold. */
LOCAL ModelStatus score_row(const float physical[MODEL_SIGNALS], Scored *scored)
{
	float scaled[MODEL_SIGNALS];
	float reconstructed[MODEL_SIGNALS];
	ModelStatus error;

	scale_row(physical, active_model_mean, active_model_std, scaled, MODEL_SIGNALS);
	error = model_run(scaled, reconstructed, &scored->cycles);
	if(error != MODEL_OK) {
		return error;
	}
	scored->score = scoring_error(scaled, reconstructed, MODEL_SIGNALS);
	scored->flagged = scored->score > THRESHOLD_SCORE;
	return MODEL_OK;
}

/* Score each physical row. */
LOCAL void scoring_task(INT stacd, void *exinf)
{
	Row row;
	Report report = {0};
	Scored scored;

	while(tk_rcv_mbf(row_mbf, &row, TMO_FEVR) == sizeof(row)) {
		if(row.no == RULE_ROWS) {
			break;
		}
		report.no = row.no;
		report.score_bits = 0;
		report.cycles = 0;
		report.flagged = 0;
		report.error = score_row(row.physical, &scored);
		if(report.error == MODEL_OK) {
			memcpy(&report.score_bits, &scored.score,
				sizeof(scored.score));
			report.cycles = scored.cycles;
			report.flagged = scored.flagged;
		}
		tk_snd_mbf(report_mbf, &report, sizeof(report), TMO_FEVR);
		if(report.error != MODEL_OK) {
			break;
		}
	}
	report.no = RULE_ROWS;
	tk_snd_mbf(report_mbf, &report, sizeof(report), TMO_FEVR);
	tk_slp_tsk(TMO_FEVR);
}

/* Print progress, decisions and inference timing over UART. */
LOCAL void report_task(INT stacd, void *exinf)
{
	Report report;
	INT flagged_rows = 0, processed = 0, errors = 0;
	UW maximum_cycles = 0;

	tm_printf((UB*)"model %s: starting %d physical rows at row %d\n",
		ACTIVE_MODEL_ID, RULE_ROWS, FIRST_ROW);
	while(tk_rcv_mbf(report_mbf, &report, TMO_FEVR) == sizeof(report)) {
		if(report.no == RULE_ROWS) {
			break;
		}
		processed++;
		flagged_rows += report.flagged;
		errors += report.error != MODEL_OK;
		if(report.cycles > maximum_cycles) {
			maximum_cycles = report.cycles;
		}
		if(processed % PROGRESS_EVERY == 0 || report.error != MODEL_OK) {
			tm_printf((UB*)"row %d score 0x%08x flagged %d cycles %u error %d\n",
				report.no, report.score_bits, report.flagged, report.cycles,
				report.error);
		}
	}
	tm_printf((UB*)"model: processed %d/%d, flagged_rows %d, dropped %d, errors %d, max_cycles %u\n",
		processed, RULE_ROWS, flagged_rows, source_dropped, errors, maximum_cycles);
	tk_slp_tsk(TMO_FEVR);
}

LOCAL T_CTSK source_ctsk = {
	.itskpri = 6, .stksz = 1024, .task = source_task,
	.tskatr = TA_HLNG | TA_RNG3,
};
LOCAL T_CTSK scoring_ctsk = {
	.itskpri = 8, .stksz = 1024, .task = scoring_task,
	.tskatr = TA_HLNG | TA_RNG3,
};
LOCAL T_CTSK report_ctsk = {
	.itskpri = 5, .stksz = 1024, .task = report_task,
	.tskatr = TA_HLNG | TA_RNG3,
};

EXPORT INT usermain(void)
{
	ID source, scoring, report;
	ModelStatus error;

	error = model_init();
	if(error != MODEL_OK) {
		tm_printf((UB*)"model init error %d\n", error);
		return error;
	}
	row_mbf = tk_cre_mbf(&row_cmbf);
	report_mbf = tk_cre_mbf(&report_cmbf);
	if(row_mbf < E_OK || report_mbf < E_OK) {
		return -10;
	}
	source = tk_cre_tsk(&source_ctsk);
	scoring = tk_cre_tsk(&scoring_ctsk);
	report = tk_cre_tsk(&report_ctsk);
	if(source < E_OK || scoring < E_OK || report < E_OK) {
		return -11;
	}
	tk_sta_tsk(report, 0);
	tk_sta_tsk(scoring, 0);
	tk_sta_tsk(source, 0);
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
