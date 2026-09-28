#ifndef INSTANT_MODEL_CONFIG_H
#define INSTANT_MODEL_CONFIG_H

/* nonlinear_ae_k8_h128_float from board/20260928-200316, with the scale of the fit
 * it came from, models/20260928-112526. */
#define INSTANT_MODEL_ID "nonlinear-ae-k8-h128-float"

static const float instant_model_mean[SIGNAL_COUNT] = {
		0x1.0585c60000000p+10f, 0x1.4013820000000p+4f,
		0x1.276ab00000000p+4f, 0x1.806a120000000p+4f,
		0x1.3c0cb00000000p+4f, 0x1.5eed540000000p+5f,
		0x1.93ac220000000p+3f, 0x1.4e3a7a0000000p+9f,
		0x1.76f1e20000000p+1f, 0x1.06b8d00000000p+10f,
		0x1.1799800000000p+3f, 0x1.23945c0000000p+3f,
		0x1.5eec2a0000000p+5f, 0x1.8a5c680000000p+0f,
		-0x1.ffeca20000000p-4f, -0x1.7bfc980000000p-10f,
		0x1.69e5b80000000p-3f,
	};

static const float instant_model_std[SIGNAL_COUNT] = {
		0x1.815c520000000p+7f, 0x1.47f0de0000000p+4f,
		0x1.280dac0000000p+4f, 0x1.5557c00000000p+4f,
		0x1.2fbb380000000p+4f, 0x1.a1a02a0000000p+4f,
		0x1.aba40c0000000p+3f, 0x1.8e09580000000p+8f,
		0x1.af87540000000p+3f, 0x1.68b16c0000000p+7f,
		0x1.bf8ea20000000p+1f, 0x1.8ce6ca0000000p+1f,
		0x1.a1a5080000000p+4f, 0x1.4b574e0000000p+2f,
		0x1.c51f0a0000000p+0f, 0x1.ecf2e40000000p-5f,
		0x1.7f7d780000000p-2f,
	};

#endif
