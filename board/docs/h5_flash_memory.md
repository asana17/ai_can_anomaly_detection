# STM32H533 flash memory

Facts about the flash of the NUCLEO-H533RE, gathered before writing alarms to it.

## Sources

- DS14539 Rev 1, the STM32H533xx datasheet: section 3.4 and tables 49 to 51.
- STM32Cube FW_H5 V1.6.0: `stm32h533xx.h`, `stm32h5xx_hal_flash.h`,
  `stm32h5xx_hal_flash_ex.h`.
- RM0481 Rev 5, the reference manual: sections 7.3.2 to 7.3.11.
- The linker script and map file of the generated CubeIDE project.

## Layout

- 512 KB in two banks of 256 KB.
- Each bank has 32 sectors of 8 KB.
- Bank 1 starts at 0x08000000 and bank 2 at 0x08040000.
- A 2 KB one-time programmable area sits at 0x08FFF000.

## Writing and erasing

- The user area is written 128 bits at a time, with ECC on each 128 bits.
- Writing a 128-bit word again without an erase is not recommended. The data and its
  ECC may no longer match.
- Writing 128 bits takes 32 us typical and 100 us at most.
- Erasing one 8 KB sector takes 2 ms typical and 10 ms at most.
- A reset during a write or an erase leaves the flash contents undefined.

## Endurance

- The program area lasts 10 000 erase cycles.
- The high-cycle data area lasts 100 000 erase cycles.
- It is the last 8 sectors of each bank, turned on per bank by an option byte.
- Its sectors shrink to 6 KB, 48 KB per bank and 96 KB in all.
- It is written 16 bits at a time and read from 0x09000000 to 0x09017FFF.
- Reading a part never written gives a double ECC error and all bits set.
- Code cannot run from it.
- RM0481 advises putting it in the bank the program is not in.

## Two banks

- One bank can be read while the other is written or erased.
- Both banks share one interface, so only one write or erase runs at a time.
- While a write runs, a read of the same bank stalls the bus until the write ends.
- The SWAP_BANK option bit swaps the addresses of the two banks after boot. Bank 1
  sits at 0x08000000 only while it is 0.
- RM0481 says to make the data area uncacheable with the MPU, since the whole range
  is cacheable by default.

## The program now

- The linker gives the program the whole 512 KB from 0x08000000.
- The last build ends near 0x08016490, about 90 KB, all in bank 1.
- The replay frames of `can_path_from_flash` are constant data in that same image.
- A program over 256 KB would spill into bank 2. Nothing stops that now.
- The HAL flash module and ICACHE are both turned on in the CubeMX project.

## Not confirmed

These need a read of the board's option bytes.

- The value of SWAP_BANK on this board.
- Whether the high-cycle data area is turned on on this board.
