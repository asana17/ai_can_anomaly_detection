#include <string.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "detect.h"
#include "mbf.h"
#include "model.h"
#include "model_config.h"
#include "moving.h"
#include "scoring.h"
#include "slots.h"
#include "threshold.h"

#define ROW_DEPTH 4
#define REPORT_DEPTH 8
#define PERIOD 100 /* ms between rows, Settings.PERIOD */
#define MAX_HOLD_ROWS 10u /* rows with no frame that end a stretch, Settings.MAX_HOLD */
#define MIN_SPEED 5.0f /* Settings.MIN_SPEED in common/settings.py */
#define HOLD 10u /* the value of Settings.HOLD the board runs */

typedef struct {
	UW no;
	float physical[MODEL_SIGNALS];
} Row;

typedef struct {
	UW no;
	UW score_bits; /* float32 score bits; avoids UART float formatting. */
	INT alarm; /* the row starts an alarm, or ends the one that was ringing */
	INT rule;
	ModelStatus error;
} Report;

/* What the CAN receive interrupt writes with slots_store(). */
EXPORT Slots bus;

LOCAL ID row_mbf, report_mbf, preprocess_id, tick_id;
LOCAL volatile UW rows_sent, rows_quiet, rows_not_ready, rows_skipped, rows_dropped, resets;
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

/* Wake preprocessing every PERIOD. */
LOCAL void tick(void *exinf)
{
	tk_wup_tsk(preprocess_id);
}

/* On each tick read the slots into a row, and send it on when the truck moves. */
LOCAL void preprocess_task(INT stacd, void *exinf)
{
	SignalState held;
	Row row, old;
	UW number = 0, seen = 0, quiet = 0, frames, intsts, i;
	INT dropped;

	while(tk_slp_tsk(TMO_FEVR) == E_OK) {
		number++;
		DI(intsts);
		frames = bus.frames;
		EI(intsts);
		if(frames == seen) {
			quiet++;
		} else {
			seen = frames;
			quiet = 0;
		}
		if(quiet == MAX_HOLD_ROWS) {
			/* what the slots hold predates the gap, as grid_sample drops it */
			DI(intsts);
			signal_state_clear(&bus.state);
			EI(intsts);
			resets++;
		}
		if(quiet > 0) {
			/* no frame since the last tick, so the row would hold only old values */
			rows_quiet++;
			continue;
		}
		for(i = 0; i < SIGNAL_STATE_SLOTS; i++) {
			DI(intsts);
			held.slots[i] = bus.state.slots[i];
			EI(intsts);
		}
		if(!signal_state_ready(&held)) {
			rows_not_ready++;
			continue;
		}
		signal_state_row(&held, row.physical);
		if(!moving(row.physical, MIN_SPEED)) {
			rows_skipped++;
			continue;
		}
		row.no = number;
		if(mbf_send_drop_oldest(row_mbf, &row, sizeof(row), &old, &dropped) != E_OK) {
			break;
		}
		rows_sent++;
		rows_dropped += dropped;
	}
	tk_stp_cyc(tick_id);
	tk_ext_tsk();
}

/* Report the row that completes HOLD flagged rows, and the row the run ends on. */
LOCAL void scoring_and_detect_task(INT stacd, void *exinf)
{
	DetectState state;
	ScoringRow scored;
	Row row;
	Report report = {0};
	INT ringing = 0, alarmed;

	detect_clear(&state);
	while(tk_rcv_mbf(row_mbf, &row, TMO_FEVR) == sizeof(row)) {
		report.error = scoring_row(row.physical, active_model_mean, active_model_std,
			MIN_SPEED, &scored);
		if(report.error != MODEL_OK) {
			report.no = row.no;
			tk_snd_mbf(report_mbf, &report, sizeof(report), TMO_FEVR);
			break;
		}
		scored_rows++;
		flagged_rows += detect_flagged(scored.score, THRESHOLD_SCORE, scored.rule_hit);
		if(scored.cycles > maximum_cycles) {
			maximum_cycles = scored.cycles;
		}
		alarmed = detect_alarmed(&state, row.no, scored.score, THRESHOLD_SCORE,
			scored.rule_hit, HOLD);
		if(alarmed != ringing) {
			report.no = row.no;
			memcpy(&report.score_bits, &scored.score, sizeof(scored.score));
			report.rule = scored.rule_hit;
			report.alarm = alarmed;
			tk_snd_mbf(report_mbf, &report, sizeof(report), TMO_FEVR);
			ringing = alarmed;
		}
	}
	tk_slp_tsk(TMO_FEVR);
}

/* Print each alarm over UART. */
LOCAL void report_task(INT stacd, void *exinf)
{
	Report report;

	tm_printf((UB*)"ai_can_anomaly_detection %s: hold %u, waiting for frames\n",
		ACTIVE_MODEL_ID, HOLD);
	while(tk_rcv_mbf(report_mbf, &report, TMO_FEVR) == sizeof(report)) {
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
	tk_slp_tsk(TMO_FEVR);
}

LOCAL T_CTSK preprocess_ctsk = {
	.itskpri = 6, .stksz = 1024, .task = preprocess_task,
	.tskatr = TA_HLNG | TA_RNG3,
};
LOCAL T_CTSK scoring_and_detect_ctsk = {
	.itskpri = 8, .stksz = 1024, .task = scoring_and_detect_task,
	.tskatr = TA_HLNG | TA_RNG3,
};
LOCAL T_CTSK report_ctsk = {
	.itskpri = 10, .stksz = 1024, .task = report_task,
	.tskatr = TA_HLNG | TA_RNG3,
};
LOCAL T_CCYC tick_ccyc = {
	.cycatr = TA_HLNG | TA_STA, .cychdr = (FP)tick,
	.cyctim = PERIOD, .cycphs = PERIOD,
};

EXPORT INT usermain(void)
{
	ID scoring_and_detect, report;
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
	preprocess_id = tk_cre_tsk(&preprocess_ctsk);
	scoring_and_detect = tk_cre_tsk(&scoring_and_detect_ctsk);
	report = tk_cre_tsk(&report_ctsk);
	if(preprocess_id < E_OK || scoring_and_detect < E_OK || report < E_OK) {
		return -11;
	}
	tk_sta_tsk(report, 0);
	tk_sta_tsk(scoring_and_detect, 0);
	tk_sta_tsk(preprocess_id, 0);
	tick_id = tk_cre_cyc(&tick_ccyc);
	if(tick_id < E_OK) {
		return -12;
	}
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
