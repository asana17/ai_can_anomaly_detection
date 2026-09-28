#include <string.h>
#include "stm32h5xx.h"
#include "model.h"
#include "instant_model.h"

_Static_assert(STAI_INSTANT_MODEL_IN_NUM == 1, "model needs one input");
_Static_assert(STAI_INSTANT_MODEL_OUT_NUM == 1, "model needs one output");
_Static_assert(STAI_INSTANT_MODEL_ACTIVATIONS_NUM == 1,
	"model needs one activation buffer");
_Static_assert(STAI_INSTANT_MODEL_IN_1_SIZE == SIGNAL_COUNT,
	"model input must contain 17 signals");
_Static_assert(STAI_INSTANT_MODEL_OUT_1_SIZE == SIGNAL_COUNT,
	"model output must contain 17 signals");
_Static_assert(STAI_INSTANT_MODEL_IN_1_FORMAT == STAI_FORMAT_FLOAT32,
	"model input must be float32");
_Static_assert(STAI_INSTANT_MODEL_OUT_1_FORMAT == STAI_FORMAT_FLOAT32,
	"model output must be float32");

/* ST Edge AI requires aligned context and activation storage. */
typedef struct {
	_Alignas(STAI_INSTANT_MODEL_CONTEXT_ALIGNMENT)
	uint8_t context[STAI_INSTANT_MODEL_CONTEXT_SIZE];
	_Alignas(STAI_INSTANT_MODEL_ACTIVATION_1_ALIGNMENT)
	uint8_t activations[STAI_INSTANT_MODEL_ACTIVATION_1_SIZE_BYTES];
	stai_ptr inputs[STAI_INSTANT_MODEL_IN_NUM];
	stai_ptr outputs[STAI_INSTANT_MODEL_OUT_NUM];
	stai_ptr activation_buffers[STAI_INSTANT_MODEL_ACTIVATIONS_NUM];
} ModelRuntime;

static ModelRuntime runtime;

ModelStatus model_init(void)
{
	stai_size count;

	if (stai_instant_model_init(runtime.context) != STAI_SUCCESS) {
		return MODEL_ERROR_INIT;
	}
	runtime.activation_buffers[0] = (stai_ptr)runtime.activations;
	if (stai_instant_model_set_activations(runtime.context, runtime.activation_buffers,
		STAI_INSTANT_MODEL_ACTIVATIONS_NUM) != STAI_SUCCESS) {
		return MODEL_ERROR_ACTIVATIONS;
	}
	/* Input and output buffers are allocated inside the activation storage. */
	if (stai_instant_model_get_inputs(runtime.context, runtime.inputs, &count) != STAI_SUCCESS ||
		count != STAI_INSTANT_MODEL_IN_NUM) {
		return MODEL_ERROR_INPUTS;
	}
	if (stai_instant_model_get_outputs(runtime.context, runtime.outputs, &count) != STAI_SUCCESS ||
		count != STAI_INSTANT_MODEL_OUT_NUM) {
		return MODEL_ERROR_OUTPUTS;
	}

	CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
	DWT->CYCCNT = 0;
	DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
	return MODEL_OK;
}

ModelStatus model_run(const float input[SIGNAL_COUNT],
	float output[SIGNAL_COUNT], uint32_t *cycles)
{
	uint32_t started;

	memcpy(runtime.inputs[0], input, SIGNAL_COUNT * sizeof(float));
	/* Measure synchronous inference only. */
	started = DWT->CYCCNT;
	if (stai_instant_model_run(runtime.context, STAI_MODE_SYNC) != STAI_SUCCESS) {
		return MODEL_ERROR_RUN;
	}
	*cycles = DWT->CYCCNT - started;
	memcpy(output, runtime.outputs[0], SIGNAL_COUNT * sizeof(float));
	return MODEL_OK;
}
