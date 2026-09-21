#ifndef BOARD_SCORING_H
#define BOARD_SCORING_H

#include <stdbool.h>
#include <stdint.h>

#include "model.h"
#include "rule_hits.h"
#include "scale.h"
#include "scoring_error.h"

typedef struct {
	float score; /* the autoencoder's score */
	bool rule_hit; /* an instant rule hits the row */
	uint32_t cycles; /* DWT cycles spent inside inference */
} ScoringRow;

/**
 * @brief Score one row with the rules and the autoencoder.
 *
 * What scoring/score.py keeps for a row, its rule flag and the model's score. The rules
 * read the physical values, the model the scaled ones.
 *
 * @param[in] physical Physical values in the order of SIGNALS.
 * @param[in] mean Training-set mean for each signal.
 * @param[in] std Training-set standard deviation for each signal.
 * @param[in] min_speed Wheel speed in km/h the moving rules start at, Settings.MIN_SPEED.
 * @param[out] scored The row's score, rule flag and inference cycles.
 * @retval MODEL_OK The row is scored.
 * @return The error model_run() returned, with only the rule flag set.
 * @pre model_init() returned MODEL_OK.
 */
static inline ModelStatus scoring_row(const float physical[MODEL_SIGNALS],
	const float mean[MODEL_SIGNALS], const float std[MODEL_SIGNALS], float min_speed,
	ScoringRow *scored)
{
	float scaled[MODEL_SIGNALS];
	float reconstructed[MODEL_SIGNALS];
	ModelStatus error;

	scored->rule_hit = rule_hits(physical, min_speed);
	scale_row(physical, mean, std, scaled, MODEL_SIGNALS);
	error = model_run(scaled, reconstructed, &scored->cycles);
	if(error != MODEL_OK) {
		return error;
	}
	scored->score = scoring_error(scaled, reconstructed, MODEL_SIGNALS);
	return MODEL_OK;
}

#endif
