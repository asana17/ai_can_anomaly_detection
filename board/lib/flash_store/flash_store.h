#ifndef FLASH_STORE_H
#define FLASH_STORE_H

#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"

/* every sector of bank 2, from the device header */
#define FLASH_STORE_SECTORS FLASH_SECTOR_NB
#define FLASH_STORE_WORD 16u    /* one Flash write, 128 bits */
/* a sector less the word its header takes */
#define FLASH_STORE_RECORD_MAX (FLASH_SECTOR_SIZE - FLASH_STORE_WORD)

/* The life we chose for the store */
#define FLASH_STORE_LIFE_YEARS 5u
#define FLASH_STORE_HOURS_A_DAY 8u
/* The erases a sector of the program area lasts, from DS14539 */
#define FLASH_STORE_SECTOR_ERASES 10000u
/*
 * The shortest time between erases that keeps every sector within its erases over the
 * life, rounded up. 164.25 s with the values above.
 */
#define FLASH_STORE_ERASE_INTERVAL_MS \
	((FLASH_STORE_LIFE_YEARS * 365ull * FLASH_STORE_HOURS_A_DAY * 3600000ull + \
		FLASH_STORE_SECTORS * FLASH_STORE_SECTOR_ERASES - 1u) / \
		(FLASH_STORE_SECTORS * FLASH_STORE_SECTOR_ERASES))

#define FLASH_STORE_ERASED 0xFFFFFFFFu /* the sector reads all 0xFF */
#define FLASH_STORE_BROKEN 0xFFFFFFFEu /* the sector has no header and is not all 0xFF */

/* The address of a sector, with bank 2 at 0x08040000 while SWAP_BANK is 0. */
#define FLASH_STORE_SECTOR_ADDRESS(sector) \
	(FLASH_BASE + FLASH_BANK_SIZE + (sector) * FLASH_SECTOR_SIZE)

/*
 * What each sector keeps in Flash in its first word, so the order and size of its record
 * outlive a reset. It is written after the record, so a sector that has it holds a whole
 * record.
 */
typedef struct {
	UW sequence; /* one more than the largest in Flash when it was written */
	UW size;     /* bytes of the record after this word */
	UW unused[2]; /* left 0, so the header fills one Flash write */
} FlashStoreSectorHeader;

/*
 * What the board keeps in RAM about bank 2 while it runs. flash_store_init makes it from
 * the sector headers, except when the next erase may start, which a reset loses.
 *
 * Bank 2 holds one record per sector. A record goes to an erased sector. When
 * none is left, the oldest sector is erased, once at any time after start and then only
 * after FLASH_STORE_ERASE_INTERVAL_MS since the last erase. Only the newest 32 records are
 * kept. Erasing the oldest one loses it.
 */
typedef struct {
	UW sector_state[FLASH_STORE_SECTORS]; /* each sector's sequence, or ERASED, or BROKEN */
	UW next_sequence;                 /* the sequence of the next record */
	UD next_erase_ms;                 /* operating time from which the next erase may start */
} FlashStoreState;

/**
 * @brief Make the store from what bank 2 holds, with the first erase free to start.
 *
 * It first checks the option bytes, and erases the sector whose write or erase the last
 * reset cut. Then each sector gets its header's sequence, or ERASED when it reads all
 * 0xFF, or else BROKEN. The next sequence is one more than the largest found, or 0.
 *
 * Call it once at start, before any write. Bank 2 is read through ICACHE, which holds
 * nothing stale only until the first write. Data left in bank 2 by anything else is read
 * as records, so bank 2 is erased once before first use.
 *
 * @param[out] store The store.
 * @return E_OK, E_NOSPT when SWAP_BANK is set or bank 2 has write protection or a
 *         high-cycle data area, or E_IO when erasing the cut sector fails.
 */
IMPORT ER flash_store_init(FlashStoreState *store);

/**
 * @brief Write a record into an erased sector, erasing the oldest one first if needed.
 *
 * The HAL waits in a loop until each erase and write ends. A broken sector counts as
 * older than any whole one. A sector whose write fails is marked broken.
 *
 * @param[in,out] store The store.
 * @param[in] record The record, 4-byte aligned.
 * @param[in] size Bytes in @p record, a multiple of FLASH_STORE_WORD up to
 *                 FLASH_STORE_RECORD_MAX.
 * @param[out] sector The sector written or tried, set unless E_PAR or E_BUSY.
 * @return E_OK, E_PAR for a bad size, E_BUSY when no sector is erased and the erase
 *         interval has not passed, or E_IO when the HAL fails.
 */
IMPORT ER flash_store_write(FlashStoreState *store, CONST void *record, UW size, UW *sector);

/**
 * @brief Copy a sector's header and find its record.
 *
 * It invalidates ICACHE first, since it may hold what the sector read before a write or
 * an erase.
 *
 * @param[in] sector The sector, below FLASH_STORE_SECTORS.
 * @param[out] header The header. Its sequence is FLASH_STORE_ERASED when the sector
 *                    holds no whole record.
 * @return The record in Flash, header->size bytes long.
 */
IMPORT CONST void *flash_store_read(UW sector, FlashStoreSectorHeader *header);

#endif
