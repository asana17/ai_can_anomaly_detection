#ifndef BOARD_SCORING_H
#define BOARD_SCORING_H

#include <stdbool.h>
#include <stdint.h>

#include "change_limit.h"
#include "model.h"
#include "recent_rows.h"
#include "repeated_signal.h"
#include "rule_hits.h"
#include "scale.h"
#include "scoring_error.h"
#include "torque_over_load.h"

typedef struct {
	float score; /* the autoencoder's score */
	bool rule_hit; /* an instant rule or a rule in rules/sequence/ hits the row */
	uint32_t cycles; /* DWT cycles spent inside inference */
} ScoringRow;

/**
 * @brief Score one row with the rules and the autoencoder.
 *
 * What scoring/score.py keeps for a row, its rule flag and the model's score. The rules
 * read the physical values, the model the scaled ones. The rules in rules/sequence/ also
 * read the rows before.
 *
 * @param[in] physical Physical values in the order of SIGNALS.
 * @param[in] rows_before The rows before @p physical since a gap.
 * @param[in] mean Training-set mean for each signal.
 * @param[in] std Training-set standard deviation for each signal.
 * @param[in] min_speed Wheel speed in km/h the moving rules start at, Settings.MIN_SPEED.
 * @param[out] scored The row's score, rule flag and inference cycles.
 * @retval MODEL_OK The row is scored.
 * @return The error model_run() returned, with only the rule flag set.
 * @pre model_init() returned MODEL_OK.
 */
static inline ModelStatus scoring_row(const float physical[SIGNAL_COUNT],
	const RecentRows *rows_before, const float mean[SIGNAL_COUNT],
	const float std[SIGNAL_COUNT], float min_speed, ScoringRow *scored)
{
	float scaled[SIGNAL_COUNT];
	float reconstructed[SIGNAL_COUNT];
	ModelStatus error;

	scored->rule_hit = rule_hits(physical, min_speed)
		|| change_limit_hits(rows_before, physical)
		|| torque_over_load_hits(rows_before, physical)
		|| repeated_signal_hits(rows_before, physical);
	scale_row(physical, mean, std, scaled, SIGNAL_COUNT);
	error = model_run(scaled, reconstructed, &scored->cycles);
	if (error != MODEL_OK) {
		return error;
	}
	scored->score = scoring_error(scaled, reconstructed, SIGNAL_COUNT);
	return MODEL_OK;
}

#endif
