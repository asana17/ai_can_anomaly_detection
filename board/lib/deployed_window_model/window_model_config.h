#ifndef WINDOW_MODEL_CONFIG_H
#define WINDOW_MODEL_CONFIG_H

/* window_delta_ae_r20_s3_k24_h128_int8 from window_board/20260929-070505, with the scale of the fit
 * it came from, window_models/20260929-004741. */
#define WINDOW_MODEL_ID "window-delta-ae-r20-s3-k24-h128-int8"

#define WINDOW_MODEL_ROWS 20u /* W, the rows of a window */

static const float window_model_mean[SIGNAL_COUNT] = {
		0x1.0037300000000p+10f, 0x1.1d63200000000p+4f,
		0x1.0409c60000000p+4f, 0x1.64b02a0000000p+4f,
		0x1.18b53c0000000p+4f, 0x1.43138c0000000p+5f,
		0x1.5c7b280000000p+3f, 0x1.33d2ee0000000p+9f,
		0x1.be0c520000000p+1f, 0x1.0184b40000000p+10f,
		0x1.10116e0000000p+3f, 0x1.1ea02a0000000p+3f,
		0x1.4310aa0000000p+5f, 0x1.b971de0000000p+0f,
		-0x1.1d6e060000000p-4f, 0x1.0b3eec0000000p-13f,
		0x1.b357ca0000000p-3f,
	};

static const float window_model_std[SIGNAL_COUNT] = {
		0x1.7932440000000p+7f, 0x1.36663e0000000p+4f,
		0x1.10a1720000000p+4f, 0x1.46630e0000000p+4f,
		0x1.1a913c0000000p+4f, 0x1.8019800000000p+4f,
		0x1.8388300000000p+3f, 0x1.6e09120000000p+8f,
		0x1.d4f00a0000000p+3f, 0x1.5bd26e0000000p+7f,
		0x1.adc3820000000p+1f, 0x1.73640e0000000p+1f,
		0x1.801d960000000p+4f, 0x1.5ae27a0000000p+2f,
		0x1.b0f12a0000000p+0f, 0x1.f377d80000000p-5f,
		0x1.7d9b260000000p-2f,
	};

#endif
