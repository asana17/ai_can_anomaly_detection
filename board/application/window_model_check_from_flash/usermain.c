#include <string.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "stm32h5xx.h"
#include "model.h"
#include "scale.h"
#include "scoring_error.h"
#include "window_model_run.h"
#include "../rule_check_from_flash/raw_rows.h"

#if RULE_SIGNALS != SIGNAL_COUNT
#error "Flash rows and the window model use different signal counts"
#endif

/* the values of a window's last row */
#define LAST_ROW ((WINDOW_MODEL_ROWS - 1u) * SIGNAL_COUNT)

LOCAL float scaled[WINDOW_MODEL_VALUES];
LOCAL float reconstructed[WINDOW_MODEL_VALUES];

/*
 * Score every window of WINDOW_MODEL_ROWS Flash rows with the window model. Print each
 * window's score as float32 bits and its inference cycles, then the fewest and most
 * cycles.
 */
EXPORT INT usermain(void)
{
	float physical[SIGNAL_COUNT];
	float score;
	UW bits, cycles, end, row, windows = 0;
	UW fewest_cycles = 0xFFFFFFFFu, most_cycles = 0;
	ModelStatus status;

	status = window_model_init();
	if (status != MODEL_OK) {
		tm_printf((UB*)"window model init error %d\n", status);
		return status;
	}
	tm_printf((UB*)"window model %s: %d rows from row %d\n", WINDOW_MODEL_ID, RULE_ROWS,
		FIRST_ROW);
	for (end = WINDOW_MODEL_ROWS - 1u; end < RULE_ROWS; end++) {
		for (row = 0; row < WINDOW_MODEL_ROWS; row++) {
			memcpy(physical, physical_rows[end + 1u - WINDOW_MODEL_ROWS + row],
				sizeof(physical));
			scale_row(physical, window_model_mean, window_model_std,
				&scaled[row * SIGNAL_COUNT], SIGNAL_COUNT);
		}
		status = window_model_run(scaled, reconstructed, &cycles);
		if (status != MODEL_OK) {
			tm_printf((UB*)"window at row %d model error %d\n", FIRST_ROW + end, status);
			return status;
		}
		score = scoring_error(&scaled[LAST_ROW], &reconstructed[LAST_ROW], SIGNAL_COUNT);
		memcpy(&bits, &score, sizeof(bits));
		tm_printf((UB*)"window at row %d score 0x%08x cycles %u\n", FIRST_ROW + end, bits,
			cycles);
		if (cycles < fewest_cycles) {
			fewest_cycles = cycles;
		}
		if (cycles > most_cycles) {
			most_cycles = cycles;
		}
		windows++;
	}
	tm_printf((UB*)"done: %u windows, %u to %u cycles at %u Hz\n", windows, fewest_cycles,
		most_cycles, SystemCoreClock);
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
