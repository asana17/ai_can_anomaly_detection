#include <string.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "stm32h5xx_hal.h"
#include "flash_store.h"

#define RECORD_WORDS (FLASH_STORE_RECORD_MAX / FLASH_STORE_WORD) /* the most a record holds */
#define WRITES 2u       /* the second meets the erase interval once every area is used */

LOCAL FlashStoreState store;
LOCAL UW record[RECORD_WORDS * FLASH_STORE_WORD / sizeof(UW)];

/* Print what each area holds. */
LOCAL void print_areas(void)
{
	UW area;

	for (area = 0; area < FLASH_STORE_AREAS; area++) {
		if (store.area_state[area] == FLASH_STORE_ERASED) {
			tm_printf((UB*)"area %u erased\n", area);
		} else if (store.area_state[area] == FLASH_STORE_BROKEN) {
			tm_printf((UB*)"area %u broken\n", area);
		} else {
			tm_printf((UB*)"area %u sequence %u\n", area, store.area_state[area]);
		}
	}
}

/* Write one record of its sequence and print the cycles it took, then read it back. */
LOCAL void write_and_read_back(void)
{
	FlashStoreAreaHeader header;
	CONST void *written;
	UW sequence = store.next_sequence;
	UW area;
	UW index, started, cycles;
	ER error;

	for (index = 0; index < sizeof(record) / sizeof(UW); index++) {
		record[index] = sequence * 0x100u + index;
	}
	started = DWT->CYCCNT;
	error = flash_store_write(&store, record, sizeof(record), &area);
	cycles = DWT->CYCCNT - started;
	if (error != E_OK) {
		tm_printf((UB*)"write of sequence %u: error %d\n", sequence, error);
		return;
	}
	written = flash_store_read(area, &header);
	if (header.sequence != sequence || header.size != sizeof(record) ||
			memcmp(written, record, sizeof(record)) != 0) {
		tm_printf((UB*)"area %u: sequence %u reads back different\n", area, sequence);
		return;
	}
	tm_printf((UB*)"area %u: sequence %u written in %u cycles at %u Hz and read back\n",
		area, sequence, cycles, SystemCoreClock);
}

EXPORT INT usermain(void)
{
	UW write;
	ER error;

	CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
	DWT->CYCCNT = 0;
	DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
	error = flash_store_init(&store);
	if (error != E_OK) {
		tm_printf((UB*)"flash store init error %d\n", error);
		tk_slp_tsk(TMO_FEVR);
	}
	print_areas();
	for (write = 0; write < WRITES; write++) {
		write_and_read_back();
	}
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
