# Test flash store

This application tests `board/lib/flash_store` on the board. At each start it prints
the state of each sector of Flash bank 2, then writes two records and reads each back.
A record is 8,176 bytes, the most a sector holds after its header, as an alarm frames
record at its largest. For each write it prints the cycles `flash_store_write` took.

A sector holds one record and each start writes two, so the 32 sectors of bank 2 are
full after 16 starts.

When no sector is erased, a write first erases the sector with the oldest record. The
store waits 164 s between two erases, but not before the first erase after a start. So
once bank 2 is full, each start writes one record. Its second write would need another
erase within 164 s, so it writes nothing and prints `error -65`, which is `E_BUSY`.

When the option bytes swap the banks, protect bank 2 or turn on its high-cycle data
area, it prints `flash store init error -9` and stops.

`STM32_Programmer_CLI` restarts the board after it reads or erases the Flash. That
start also writes two records, so right after erasing bank 2, sectors 0 and 1 already
hold records.

## Before the first run

Erase bank 2 once, as [flash.md](../../docs/flash.md) describes.

## Prepare, build and flash

```sh
python3 -m board.prepare CUBEIDE_PROJECT_DIR test_flash_store
python3 board/flash.py CUBEIDE_PROJECT_DIR
```

Reset the board over SWD to start it again:

```sh
STM32_Programmer_CLI -c port=SWD -rst
```

## Result

On 2026-09-29 the Release build, at `-O2` and 32 MHz, wrote into sectors already
erased and printed

```
sector 12: sequence 12 written in 609707 cycles at 32000000 Hz and read back
sector 13: sequence 13 written in 611112 cycles at 32000000 Hz and read back
```

A record of 8,176 bytes took about 19.1 ms to write.
