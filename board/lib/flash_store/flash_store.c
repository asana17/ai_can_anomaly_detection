#include "flash_store.h"

/* The kernel's operating time in milliseconds. */
LOCAL UD now_ms(void)
{
	SYSTIM now;

	tk_get_otm(&now);
	return ((UD)(UW)now.hi << 32) | now.lo;
}

/* Whether every word of the sector reads all bits set. */
LOCAL BOOL is_erased(UW sector)
{
	CONST volatile UW *word = (CONST volatile UW *)FLASH_STORE_SECTOR_ADDRESS(sector);
	UW index;

	for (index = 0; index < FLASH_SECTOR_SIZE / sizeof(UW); index++) {
		if (word[index] != 0xFFFFFFFFu) {
			return FALSE;
		}
	}
	return TRUE;
}

/*
 * The sector with no header first, since it holds no whole record, else the one with
 * the smallest sequence. Called only when no sector is erased, so ERASED is never among
 * them.
 */
LOCAL UW oldest(CONST FlashStoreState *store)
{
	UW sector;
	UW found = 0;

	for (sector = 0; sector < FLASH_STORE_SECTORS; sector++) {
		if (store->sector_state[sector] == FLASH_STORE_BROKEN) {
			return sector;
		}
		if (store->sector_state[sector] < store->sector_state[found]) {
			found = sector;
		}
	}
	return found;
}

/*
 * Erase a sector. The next erase time is set before the erase, so a failed erase also
 * waits out the interval, since it may have worn the sector too.
 */
LOCAL ER erase(FlashStoreState *store, UW sector)
{
	FLASH_EraseInitTypeDef init = {0};
	uint32_t failed;

	init.TypeErase = FLASH_TYPEERASE_SECTORS;
	init.Banks = FLASH_BANK_2;
	init.Sector = sector;
	init.NbSectors = 1u;
	store->next_erase_ms = now_ms() + FLASH_STORE_ERASE_INTERVAL_MS;
	if (HAL_FLASHEx_Erase(&init, &failed) != HAL_OK) {
		store->sector_state[sector] = FLASH_STORE_BROKEN;
		return E_IO;
	}
	store->sector_state[sector] = FLASH_STORE_ERASED;
	return E_OK;
}

/*
 * Write the record, then the header over the first word. The sector counts as broken
 * until the header is in, so a failed write leaves it to be erased first.
 */
LOCAL ER program(FlashStoreState *store, UW sector, CONST void *record, UW size)
{
	UW address = FLASH_STORE_SECTOR_ADDRESS(sector);
	CONST UB *data = record;
	FlashStoreSectorHeader header = {0};
	UW offset;

	store->sector_state[sector] = FLASH_STORE_BROKEN;
	for (offset = 0; offset < size; offset += FLASH_STORE_WORD) {
		if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_QUADWORD, address + FLASH_STORE_WORD + offset,
				(uint32_t)(data + offset)) != HAL_OK) {
			return E_IO;
		}
	}
	header.sequence = store->next_sequence;
	header.size = size;
	if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_QUADWORD, address, (uint32_t)&header) != HAL_OK) {
		return E_IO;
	}
	store->sector_state[sector] = store->next_sequence;
	store->next_sequence = store->next_sequence + 1u;
	return E_OK;
}

/* Whether the option bytes let the store use bank 2 as it assumes. */
LOCAL BOOL bank_2_usable(void)
{
	FLASH_OBProgramInitTypeDef options = {0};

	options.Banks = FLASH_BANK_2;
	HAL_FLASHEx_OBGetConfig(&options);
	/* swapped banks put the program at 0x08040000 */
	if ((options.USERConfig & OB_USER_SWAP_BANK) != 0) {
		return FALSE;
	}
	/* a protected sector can be neither erased nor written */
	if (options.WRPState != OB_WRPSTATE_DISABLE) {
		return FALSE;
	}
	/* a high-cycle data area turns the last 8 sectors into 6 KB ones at another address */
	if (options.EDATASize != 0) {
		return FALSE;
	}
	return TRUE;
}

/*
 * The bank 2 sector whose write or erase the last reset cut, or FLASH_STORE_SECTORS if
 * none. The address is taken as a byte offset in the bank, as the HAL describes it.
 * RM0481 table 54 lists a range that reads as 16-byte words instead.
 */
LOCAL UW interrupted_sector(void)
{
	FLASH_OperationTypeDef operation;

	HAL_FLASHEx_GetOperation(&operation);
	if (operation.OperationType != FLASH_OPERATION_TYPE_QUADWORD &&
			operation.OperationType != FLASH_OPERATION_TYPE_SECTORERASE) {
		return FLASH_STORE_SECTORS;
	}
	if (operation.FlashArea != FLASH_OPERATION_AREA_BANK_2) {
		return FLASH_STORE_SECTORS;
	}
	return operation.Address / FLASH_SECTOR_SIZE;
}

EXPORT ER flash_store_init(FlashStoreState *store)
{
	CONST volatile FlashStoreSectorHeader *header;
	UW sector;
	ER error;

	if (!bank_2_usable()) {
		return E_NOSPT;
	}
	store->next_sequence = 0;
	/* the operating time starts at 0, so the first erase does not wait */
	store->next_erase_ms = 0;
	/*
	 * A word the reset cut may fail its ECC, and reading it raises an NMI that RM0481
	 * lets no mask stop for this area. RM0481 says to erase such a sector again.
	 */
	sector = interrupted_sector();
	if (sector < FLASH_STORE_SECTORS) {
		HAL_FLASH_Unlock();
		error = erase(store, sector);
		HAL_FLASH_Lock();
		if (error != E_OK) {
			return error;
		}
	}
	for (sector = 0; sector < FLASH_STORE_SECTORS; sector++) {
		header = (CONST volatile FlashStoreSectorHeader *)FLASH_STORE_SECTOR_ADDRESS(sector);
		/* a header is written last, so a sector with one holds a whole record */
		if (header->sequence != FLASH_STORE_ERASED) {
			store->sector_state[sector] = header->sequence;
			if (header->sequence >= store->next_sequence) {
				store->next_sequence = header->sequence + 1u;
			}
		} else if (is_erased(sector)) { /* no header, and nothing else written either */
			store->sector_state[sector] = FLASH_STORE_ERASED;
		} else {
			store->sector_state[sector] = FLASH_STORE_BROKEN;
		}
	}
	return E_OK;
}

EXPORT ER flash_store_write(FlashStoreState *store, CONST void *record, UW size, UW *sector)
{
	ER error = E_OK;
	UW found;

	if (size % FLASH_STORE_WORD != 0 || size > FLASH_STORE_RECORD_MAX) {
		return E_PAR;
	}
	for (found = 0; found < FLASH_STORE_SECTORS; found++) {
		if (store->sector_state[found] == FLASH_STORE_ERASED) {
			break;
		}
	}
	/*
	 * The first erase after start does not wait, so a cut right after a reset is kept.
	 * Only a write erases, so a reset alone wears nothing.
	 */
	if (found == FLASH_STORE_SECTORS && now_ms() < store->next_erase_ms) {
		return E_BUSY;
	}
	HAL_FLASH_Unlock(); /* erase and write need the control register unlocked */
	if (found == FLASH_STORE_SECTORS) {
		found = oldest(store);
		error = erase(store, found);
	}
	if (error == E_OK) {
		error = program(store, found, record, size);
	}
	HAL_FLASH_Lock();
	*sector = found;
	return error;
}

EXPORT CONST void *flash_store_read(UW sector, FlashStoreSectorHeader *header)
{
	HAL_ICACHE_Invalidate();
	*header = *(CONST FlashStoreSectorHeader *)FLASH_STORE_SECTOR_ADDRESS(sector);
	return (CONST void *)(FLASH_STORE_SECTOR_ADDRESS(sector) + FLASH_STORE_WORD);
}
