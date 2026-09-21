#include "scale.h"

void scale_row(const float physical[], const float mean[], const float std[],
	float scaled[], size_t signals)
{
	size_t i;

	for(i = 0; i < signals; i++) {
		scaled[i] = (physical[i] - mean[i]) / std[i];
	}
}
