#include <string.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "model.h"
#include "scale.h"
#include "model_config.h"
#include "../rule_check_from_flash/raw_rows.h"

#if RULE_SIGNALS != MODEL_SIGNALS
#error "Flash rows and the selected model use different signal counts"
#endif

/* Mean squared error between the scaled row and its reconstruction. */
LOCAL float reconstruction_error(const float scaled[MODEL_SIGNALS],
	const float reconstructed[MODEL_SIGNALS])
{
	float total = 0.0f;
	UW i;

	for(i = 0; i < MODEL_SIGNALS; i++) {
		const float difference = scaled[i] - reconstructed[i];
		total += difference * difference;
	}
	return total / MODEL_SIGNALS;
}

/* Print every Flash row's reconstruction and reconstruction error as float32 bits, and
 * its inference cycles. */
EXPORT INT usermain(void)
{
	float physical[MODEL_SIGNALS];
	float scaled[MODEL_SIGNALS];
	float reconstructed[MODEL_SIGNALS];
	float error;
	UW bits, cycles, i, j;
	ModelStatus status;

	status = model_init();
	if(status != MODEL_OK) {
		tm_printf((UB*)"model init error %d\n", status);
		return status;
	}
	tm_printf((UB*)"model %s: %d rows from row %d\n", ACTIVE_MODEL_ID, RULE_ROWS,
		FIRST_ROW);
	for(i = 0; i < RULE_ROWS; i++) {
		memcpy(physical, physical_rows[i], sizeof(physical));
		scale_row(physical, active_model_mean, active_model_std, scaled, MODEL_SIGNALS);
		status = model_run(scaled, reconstructed, &cycles);
		if(status != MODEL_OK) {
			tm_printf((UB*)"row %d model error %d\n", FIRST_ROW + i, status);
			return status;
		}
		tm_printf((UB*)"row %d reconstruction", FIRST_ROW + i);
		for(j = 0; j < MODEL_SIGNALS; j++) {
			memcpy(&bits, &reconstructed[j], sizeof(bits));
			tm_printf((UB*)" 0x%08x", bits);
		}
		tm_printf((UB*)"\n");
		error = reconstruction_error(scaled, reconstructed);
		memcpy(&bits, &error, sizeof(bits));
		tm_printf((UB*)"row %d reconstruction_error 0x%08x cycles %u\n",
			FIRST_ROW + i, bits, cycles);
	}
	tm_printf((UB*)"done: %d rows\n", RULE_ROWS);
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
