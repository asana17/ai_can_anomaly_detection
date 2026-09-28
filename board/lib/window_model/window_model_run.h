#ifndef BOARD_WINDOW_MODEL_RUN_H
#define BOARD_WINDOW_MODEL_RUN_H

#include <stdint.h>
#include "model.h"
#include "window_model_config.h"

/* The values of one window, its WINDOW_MODEL_ROWS rows of SIGNAL_COUNT, oldest first. */
#define WINDOW_MODEL_VALUES (WINDOW_MODEL_ROWS * SIGNAL_COUNT)

/**
 * @brief Initialize the generated st-ai window model linked into the application.
 *
 * The build must provide `window_model.h`, `window_model.c` and its generated data
 * files. The model has one int8 input and output of WINDOW_MODEL_VALUES values.
 *
 * @retval MODEL_OK Initialization completed.
 * @retval MODEL_ERROR_INIT Context initialization failed.
 * @retval MODEL_ERROR_ACTIVATIONS Activation-buffer setup failed.
 * @retval MODEL_ERROR_INPUTS The generated input buffer was not found.
 * @retval MODEL_ERROR_OUTPUTS The generated output buffer was not found.
 */
ModelStatus window_model_init(void);

/**
 * @brief Run one synchronous inference of the window model on an initialized model.
 *
 * The window is quantized to the model's int8 input, and its int8 output is turned back
 * into floats.
 *
 * @param[in] input Scaled model-space window, oldest row first.
 * @param[out] output Reconstructed model-space window.
 * @param[out] cycles DWT cycle count spent inside st-ai inference.
 * @retval MODEL_OK Inference completed.
 * @retval MODEL_ERROR_RUN st-ai rejected the run.
 * @pre window_model_init() returned MODEL_OK.
 */
ModelStatus window_model_run(const float input[WINDOW_MODEL_VALUES],
	float output[WINDOW_MODEL_VALUES], uint32_t *cycles);

#endif
