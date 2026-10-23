#include <string.h>
#include "stm32h5xx.h"
#include "window_model_run.h"
#include "window_model.h"

_Static_assert(STAI_WINDOW_MODEL_IN_NUM == 1, "window model needs one input");
_Static_assert(STAI_WINDOW_MODEL_OUT_NUM == 1, "window model needs one output");
_Static_assert(STAI_WINDOW_MODEL_ACTIVATIONS_NUM == 1,
	"window model needs one activation buffer");
_Static_assert(STAI_WINDOW_MODEL_IN_1_SIZE == WINDOW_MODEL_VALUES,
	"window model input must hold one window");
_Static_assert(STAI_WINDOW_MODEL_OUT_1_SIZE == WINDOW_MODEL_VALUES,
	"window model output must hold one window");

/* An int8 model comes with the scale of its input, a float one does not. */
#ifdef STAI_WINDOW_MODEL_IN_1_SCALE
#define WINDOW_MODEL_INT8
_Static_assert(STAI_WINDOW_MODEL_IN_1_FORMAT == STAI_FORMAT_S8,
	"window model input must be int8");
_Static_assert(STAI_WINDOW_MODEL_OUT_1_FORMAT == STAI_FORMAT_S8,
	"window model output must be int8");
#else
_Static_assert(STAI_WINDOW_MODEL_IN_1_FORMAT == STAI_FORMAT_FLOAT32,
	"window model input must be float");
_Static_assert(STAI_WINDOW_MODEL_OUT_1_FORMAT == STAI_FORMAT_FLOAT32,
	"window model output must be float");
#endif

/* ST Edge AI requires aligned context and activation storage. */
typedef struct {
	_Alignas(STAI_WINDOW_MODEL_CONTEXT_ALIGNMENT)
	uint8_t context[STAI_WINDOW_MODEL_CONTEXT_SIZE];
	_Alignas(STAI_WINDOW_MODEL_ACTIVATION_1_ALIGNMENT)
	uint8_t activations[STAI_WINDOW_MODEL_ACTIVATION_1_SIZE_BYTES];
	stai_ptr inputs[STAI_WINDOW_MODEL_IN_NUM];
	stai_ptr outputs[STAI_WINDOW_MODEL_OUT_NUM];
	stai_ptr activation_buffers[STAI_WINDOW_MODEL_ACTIVATIONS_NUM];
} WindowModelRuntime;

static WindowModelRuntime runtime;

#ifdef WINDOW_MODEL_INT8
/* value on the input's int8 grid, rounded to the nearest step and held in int8 */
static int8_t quantized(float value)
{
	float step = value / STAI_WINDOW_MODEL_IN_1_SCALE + STAI_WINDOW_MODEL_IN_1_ZERO_POINT;
	int32_t rounded;

	if (step >= 0.0f) {
		rounded = (int32_t)(step + 0.5f);
	} else {
		rounded = (int32_t)(step - 0.5f);
	}
	if (rounded > INT8_MAX) {
		return INT8_MAX;
	}
	if (rounded < INT8_MIN) {
		return INT8_MIN;
	}
	return (int8_t)rounded;
}
#endif

ModelStatus window_model_init(void)
{
	stai_size count;

	if (stai_window_model_init(runtime.context) != STAI_SUCCESS) {
		return MODEL_ERROR_INIT;
	}
	runtime.activation_buffers[0] = (stai_ptr)runtime.activations;
	if (stai_window_model_set_activations(runtime.context, runtime.activation_buffers,
		STAI_WINDOW_MODEL_ACTIVATIONS_NUM) != STAI_SUCCESS) {
		return MODEL_ERROR_ACTIVATIONS;
	}
	/* Input and output buffers are allocated inside the activation storage. */
	if (stai_window_model_get_inputs(runtime.context, runtime.inputs, &count) != STAI_SUCCESS ||
		count != STAI_WINDOW_MODEL_IN_NUM) {
		return MODEL_ERROR_INPUTS;
	}
	if (stai_window_model_get_outputs(runtime.context, runtime.outputs, &count) != STAI_SUCCESS ||
		count != STAI_WINDOW_MODEL_OUT_NUM) {
		return MODEL_ERROR_OUTPUTS;
	}

	CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
	DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
	return MODEL_OK;
}

ModelStatus window_model_run(const float input[WINDOW_MODEL_VALUES],
	float output[WINDOW_MODEL_VALUES], uint32_t *cycles)
{
	uint32_t started;
#ifdef WINDOW_MODEL_INT8
	int8_t *in = (int8_t *)runtime.inputs[0];
	const int8_t *out = (const int8_t *)runtime.outputs[0];
	uint32_t index;

	for (index = 0; index < WINDOW_MODEL_VALUES; index++) {
		in[index] = quantized(input[index]);
	}
#else
	memcpy(runtime.inputs[0], input, WINDOW_MODEL_VALUES * sizeof(float));
#endif
	/* Measure synchronous inference only. */
	started = DWT->CYCCNT;
	if (stai_window_model_run(runtime.context, STAI_MODE_SYNC) != STAI_SUCCESS) {
		return MODEL_ERROR_RUN;
	}
	*cycles = DWT->CYCCNT - started;
#ifdef WINDOW_MODEL_INT8
	for (index = 0; index < WINDOW_MODEL_VALUES; index++) {
		output[index] = (float)(out[index] - STAI_WINDOW_MODEL_OUT_1_ZERO_POINT)
			* STAI_WINDOW_MODEL_OUT_1_SCALE;
	}
#else
	memcpy(output, runtime.outputs[0], WINDOW_MODEL_VALUES * sizeof(float));
#endif
	return MODEL_OK;
}
