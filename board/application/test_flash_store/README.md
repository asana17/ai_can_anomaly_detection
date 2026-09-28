# Test flash store

This application tests `board/lib/flash_store` on the board. At each start it prints
the state of each sector of Flash bank 2, then writes two records of 64 bytes and reads
each back.

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
