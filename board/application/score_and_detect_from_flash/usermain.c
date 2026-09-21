#include <string.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "detector.h"
#include "mbf.h"
#include "model.h"
#include "model_config.h"
#include "moving.h"
#include "rule_hits.h"
#include "scale.h"
#include "threshold.h"
#include "../rule_check_from_flash/raw_rows.h"

#if RULE_SIGNALS != MODEL_SIGNALS
#error "Flash rows and the selected model use different signal counts"
#endif

#define ROW_DEPTH 4
#define REPORT_DEPTH 8
#define MIN_SPEED 5.0f /* Settings.MIN_SPEED in common/settings.py */
#define HOLD 10u /* the value of Settings.HOLD the board runs */

typedef struct {
	UW no;
	float physical[RULE_SIGNALS];
} Row;

typedef struct {
	UW no;
	UW score_bits; /* float32 score bits; avoids UART float formatting. */
	INT alarm; /* the row starts an alarm, or ends the one that was ringing */
	INT rule;
	ModelStatus error;
} Report;

typedef struct {
	float score;
	UW cycles;
	INT rule;
} Detection;

LOCAL ID row_mbf, report_mbf;
LOCAL volatile INT preprocess_dropped, preprocess_skipped;
LOCAL volatile UW scored_rows, flagged_rows, maximum_cycles;

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

/* Send the Flash rows above MIN_SPEED every 100 ms. */
LOCAL void preprocess_task(INT stacd, void *exinf)
{
	Row row = {0}, old;
	INT dropped;
	UW i;

	for(i = 0; i < RULE_ROWS; i++) {
		memcpy(row.physical, physical_rows[i], sizeof(row.physical));
		if(moving(row.physical, MIN_SPEED)) {
			row.no = i;
			if(mbf_send_drop_oldest(row_mbf, &row, sizeof(row), &old,
				&dropped) != E_OK) {
				break;
			}
			preprocess_dropped += dropped;
		} else {
			preprocess_skipped++;
		}
		tk_dly_tsk(100);
	}
	row.no = RULE_ROWS;
	tk_snd_mbf(row_mbf, &row, sizeof(row), TMO_FEVR);
	tk_slp_tsk(TMO_FEVR);
}

/* Score one row with the rules and the autoencoder. */
LOCAL ModelStatus score_row(const float physical[MODEL_SIGNALS], Detection *detection)
{
	float scaled[MODEL_SIGNALS];
	float reconstructed[MODEL_SIGNALS];
	float total = 0.0f;
	UW i;
	ModelStatus error;

	detection->rule = rule_hits(physical, MIN_SPEED);
	scale_row(physical, active_model_mean, active_model_std, scaled, MODEL_SIGNALS);
	error = model_run(scaled, reconstructed, &detection->cycles);
	if(error != MODEL_OK) {
		return error;
	}
	for(i = 0; i < MODEL_SIGNALS; i++) {
		const float difference = scaled[i] - reconstructed[i];
		total += difference * difference;
	}
	detection->score = total / MODEL_SIGNALS;
	return MODEL_OK;
}

/* Report the row that completes HOLD flagged rows, and the row the run ends on. */
LOCAL void score_and_detect_task(INT stacd, void *exinf)
{
	Detector state;
	Detection detection;
	Row row;
	Report report = {0};
	INT ringing = 0, alarmed;

	detector_clear(&state);
	while(tk_rcv_mbf(row_mbf, &row, TMO_FEVR) == sizeof(row)) {
		if(row.no == RULE_ROWS) {
			break;
		}
		report.error = score_row(row.physical, &detection);
		if(report.error != MODEL_OK) {
			report.no = row.no;
			tk_snd_mbf(report_mbf, &report, sizeof(report), TMO_FEVR);
			break;
		}
		scored_rows++;
		flagged_rows += detector_flagged(detection.score, THRESHOLD_SCORE,
			detection.rule);
		if(detection.cycles > maximum_cycles) {
			maximum_cycles = detection.cycles;
		}
		alarmed = detector_alarmed(&state, row.no, detection.score, THRESHOLD_SCORE,
			detection.rule, HOLD);
		if(alarmed != ringing) {
			report.no = row.no;
			memcpy(&report.score_bits, &detection.score, sizeof(detection.score));
			report.rule = detection.rule;
			report.alarm = alarmed;
			tk_snd_mbf(report_mbf, &report, sizeof(report), TMO_FEVR);
			ringing = alarmed;
		}
	}
	report.no = RULE_ROWS;
	tk_snd_mbf(report_mbf, &report, sizeof(report), TMO_FEVR);
	tk_slp_tsk(TMO_FEVR);
}

/* Print each alarm and what the run covered over UART. */
LOCAL void report_task(INT stacd, void *exinf)
{
	Report report;
	INT alarms = 0, errors = 0;

	tm_printf((UB*)"score_and_detect %s: starting %d rows at row %d, hold %u\n",
		ACTIVE_MODEL_ID, RULE_ROWS, FIRST_ROW, HOLD);
	while(tk_rcv_mbf(report_mbf, &report, TMO_FEVR) == sizeof(report)) {
		if(report.no == RULE_ROWS) {
			break;
		}
		if(report.error != MODEL_OK) {
			errors++;
			tm_printf((UB*)"row %d error %d\n", FIRST_ROW + report.no,
				report.error);
			continue;
		}
		alarms += report.alarm;
		if(report.alarm) {
			tm_printf((UB*)"alarm start at row %d score 0x%08x rule %d\n",
				FIRST_ROW + report.no, report.score_bits, report.rule);
		} else {
			tm_printf((UB*)"alarm end at row %d score 0x%08x rule %d\n",
				FIRST_ROW + report.no, report.score_bits, report.rule);
		}
	}
	tm_printf((UB*)"score_and_detect: scored %u/%d, skipped %d, flagged_rows %u, alarms %d,"
		" dropped %d, errors %d, max_cycles %u\n",
		scored_rows, RULE_ROWS, preprocess_skipped, flagged_rows, alarms,
		preprocess_dropped, errors, maximum_cycles);
	tk_slp_tsk(TMO_FEVR);
}

LOCAL T_CTSK preprocess_ctsk = {
	.itskpri = 6, .stksz = 1024, .task = preprocess_task,
	.tskatr = TA_HLNG | TA_RNG3,
};
LOCAL T_CTSK score_and_detect_ctsk = {
	.itskpri = 8, .stksz = 1024, .task = score_and_detect_task,
	.tskatr = TA_HLNG | TA_RNG3,
};
LOCAL T_CTSK report_ctsk = {
	.itskpri = 5, .stksz = 1024, .task = report_task,
	.tskatr = TA_HLNG | TA_RNG3,
};

EXPORT INT usermain(void)
{
	ID preprocess, score_and_detect, report;
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
	preprocess = tk_cre_tsk(&preprocess_ctsk);
	score_and_detect = tk_cre_tsk(&score_and_detect_ctsk);
	report = tk_cre_tsk(&report_ctsk);
	if(preprocess < E_OK || score_and_detect < E_OK || report < E_OK) {
		return -11;
	}
	tk_sta_tsk(report, 0);
	tk_sta_tsk(score_and_detect, 0);
	tk_sta_tsk(preprocess, 0);
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
