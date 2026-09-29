# Test flash store

This application tests `board/lib/flash_store` on the board. At each start it prints
the state of each area of Flash bank 2, then writes two records and reads each back.
An area is 4 sectors, 32 KB. A record is 32,752 bytes, the most an area holds after its
header. For each write it prints the cycles `flash_store_write` took.

An area holds one record and each start writes two, so the 8 areas of bank 2 are full
after 4 starts.

When no area is erased, a write first erases the area with the oldest record, all 4
sectors of it. The store waits 657 s between two erases, but not before the first erase
after a start. So once bank 2 is full, each start writes one record. Its second write
would need another erase within 657 s, so it writes nothing and prints `error -65`,
which is `E_BUSY`.

When the option bytes swap the banks, protect bank 2 or turn on its high-cycle data
area, it prints `flash store init error -9` and stops.

`STM32_Programmer_CLI` restarts the board after it reads or erases the Flash. That
start also writes two records, so right after erasing bank 2, areas 0 and 1 already
hold records.

## Before the first run

Erase bank 2 once, as [flash.md](../../docs/flash.md) describes.

## Prepare, build and flash

```sh
python3 -m board.prepare test_flash_store
python3 -m board.flash
```

Reset the board over SWD to start it again:

```sh
STM32_Programmer_CLI -c port=SWD -rst
```

## Result

On 2026-09-29 the Release build, at `-O2` and 32 MHz, wrote into areas already erased
and printed

```
area 0: sequence 0 written in 2438480 cycles at 32000000 Hz and read back
area 1: sequence 1 written in 2440274 cycles at 32000000 Hz and read back
```

A record of 32,752 bytes took about 76.2 ms to write. After 3 more starts every area
held a record. The next start erased area 0 and wrote sequence 8 into it in 2,634,674
cycles, about 82.3 ms, and its second write printed `error -65`.
