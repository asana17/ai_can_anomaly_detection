#ifndef BOARD_MODEL_H
#define BOARD_MODEL_H

#include <stdint.h>

#define MODEL_SIGNALS 17

/** @brief Result of model initialization or inference. */
typedef enum {
	MODEL_OK = 0, /**< Operation completed successfully. */
	MODEL_ERROR_INIT = -1, /**< st-ai rejected context initialization. */
	MODEL_ERROR_ACTIVATIONS = -2, /**< Activation-buffer setup failed. */
	MODEL_ERROR_INPUTS = -3, /**< The generated input buffer was not found. */
	MODEL_ERROR_OUTPUTS = -4, /**< The generated output buffer was not found. */
	MODEL_ERROR_RUN = -5, /**< st-ai rejected synchronous inference. */
} ModelStatus;

/**
 * @brief Initialize the generated st-ai model linked into the application.
 *
 * The build must provide `active_model.h`, `active_model.c` and its generated data
 * files. The model has one float32 input and output of MODEL_SIGNALS values.
 *
 * @retval MODEL_OK Initialization completed.
 * @retval MODEL_ERROR_INIT Context initialization failed.
 * @retval MODEL_ERROR_ACTIVATIONS Activation-buffer setup failed.
 * @retval MODEL_ERROR_INPUTS The generated input buffer was not found.
 * @retval MODEL_ERROR_OUTPUTS The generated output buffer was not found.
 */
ModelStatus model_init(void);

/**
 * @brief Run one synchronous inference on an initialized model.
 *
 * @param[in] input Scaled model-space row, not physical signal values.
 * @param[out] output Reconstructed model-space row.
 * @param[out] cycles DWT cycle count spent inside st-ai inference.
 * @retval MODEL_OK Inference completed.
 * @retval MODEL_ERROR_RUN st-ai rejected the run.
 * @pre model_init() returned MODEL_OK.
 */
ModelStatus model_run(const float input[MODEL_SIGNALS],
	float output[MODEL_SIGNALS], uint32_t *cycles);

#endif
