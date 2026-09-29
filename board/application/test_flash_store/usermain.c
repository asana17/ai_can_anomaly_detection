#include <string.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "stm32h5xx_hal.h"
#include "flash_store.h"

#define RECORD_WORDS (FLASH_STORE_RECORD_MAX / FLASH_STORE_WORD) /* the most a record holds */
#define WRITES 2u       /* the second meets the erase interval once every sector is used */

LOCAL FlashStoreState store;
LOCAL UW record[RECORD_WORDS * FLASH_STORE_WORD / sizeof(UW)];

/* Print what each sector holds. */
LOCAL void print_sectors(void)
{
	UW sector;

	for (sector = 0; sector < FLASH_STORE_SECTORS; sector++) {
		if (store.sector_state[sector] == FLASH_STORE_ERASED) {
			tm_printf((UB*)"sector %u erased\n", sector);
		} else if (store.sector_state[sector] == FLASH_STORE_BROKEN) {
			tm_printf((UB*)"sector %u broken\n", sector);
		} else {
			tm_printf((UB*)"sector %u sequence %u\n", sector, store.sector_state[sector]);
		}
	}
}

/* Write one record of its sequence and print the cycles it took, then read it back. */
LOCAL void write_and_read_back(void)
{
	FlashStoreSectorHeader header;
	CONST void *written;
	UW sequence = store.next_sequence;
	UW sector;
	UW index, started, cycles;
	ER error;

	for (index = 0; index < sizeof(record) / sizeof(UW); index++) {
		record[index] = sequence * 0x100u + index;
	}
	started = DWT->CYCCNT;
	error = flash_store_write(&store, record, sizeof(record), &sector);
	cycles = DWT->CYCCNT - started;
	if (error != E_OK) {
		tm_printf((UB*)"write of sequence %u: error %d\n", sequence, error);
		return;
	}
	written = flash_store_read(sector, &header);
	if (header.sequence != sequence || header.size != sizeof(record) ||
			memcmp(written, record, sizeof(record)) != 0) {
		tm_printf((UB*)"sector %u: sequence %u reads back different\n", sector, sequence);
		return;
	}
	tm_printf((UB*)"sector %u: sequence %u written in %u cycles at %u Hz and read back\n",
		sector, sequence, cycles, SystemCoreClock);
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
	print_sectors();
	for (write = 0; write < WRITES; write++) {
		write_and_read_back();
	}
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
