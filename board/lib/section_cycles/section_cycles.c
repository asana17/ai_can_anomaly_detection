#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"
#include "section_cycles.h"

EXPORT SectionCycles section_cycles[SECTION_COUNT];

EXPORT void section_cycles_clear(void)
{
	UW i;

	for (i = 0; i < SECTION_COUNT; i++) {
		section_cycles[i].fewest = 0xFFFFFFFFu;
		section_cycles[i].most = 0;
	}
}

EXPORT UW section_cycles_start(void)
{
	return DWT->CYCCNT;
}

EXPORT void section_cycles_end(Section section, UW started)
{
	section_cycles_add(section, DWT->CYCCNT - started);
}

EXPORT void section_cycles_add(Section section, UW cycles)
{
	if (cycles < section_cycles[section].fewest) {
		section_cycles[section].fewest = cycles;
	}
	if (cycles > section_cycles[section].most) {
		section_cycles[section].most = cycles;
	}
}
