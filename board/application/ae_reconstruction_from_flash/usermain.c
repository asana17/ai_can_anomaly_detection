#include <string.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "model.h"
#include "scale.h"
#include "scoring_error.h"
#include "model_config.h"
#include "../rule_check_from_flash/raw_rows.h"

#if RULE_SIGNALS != SIGNAL_COUNT
#error "Flash rows and the selected model use different signal counts"
#endif

/* Print every Flash row's reconstruction and reconstruction error as float32 bits, and
 * its inference cycles. */
EXPORT INT usermain(void)
{
	float physical[SIGNAL_COUNT];
	float scaled[SIGNAL_COUNT];
	float reconstructed[SIGNAL_COUNT];
	float error;
	UW bits, cycles, i, j;
	ModelStatus status;

	status = model_init();
	if (status != MODEL_OK) {
		tm_printf((UB*)"model init error %d\n", status);
		return status;
	}
	tm_printf((UB*)"model %s: %d rows from row %d\n", INSTANT_MODEL_ID, RULE_ROWS,
		FIRST_ROW);
	for (i = 0; i < RULE_ROWS; i++) {
		memcpy(physical, physical_rows[i], sizeof(physical));
		scale_row(physical, instant_model_mean, instant_model_std, scaled, SIGNAL_COUNT);
		status = model_run(scaled, reconstructed, &cycles);
		if (status != MODEL_OK) {
			tm_printf((UB*)"row %d model error %d\n", FIRST_ROW + i, status);
			return status;
		}
		tm_printf((UB*)"row %d reconstruction", FIRST_ROW + i);
		for (j = 0; j < SIGNAL_COUNT; j++) {
			memcpy(&bits, &reconstructed[j], sizeof(bits));
			tm_printf((UB*)" 0x%08x", bits);
		}
		tm_printf((UB*)"\n");
		error = scoring_error(scaled, reconstructed, SIGNAL_COUNT);
		memcpy(&bits, &error, sizeof(bits));
		tm_printf((UB*)"row %d reconstruction_error 0x%08x cycles %u\n",
			FIRST_ROW + i, bits, cycles);
	}
	tm_printf((UB*)"done: %d rows\n", RULE_ROWS);
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
