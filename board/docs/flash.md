# Flash from the command line

`board/flash.py` builds an already prepared CubeIDE project without opening the GUI,
then writes, verifies and resets the connected board. Application selection belongs to
`board.prepare` and is a separate command.

## Current limitation

The script currently supports macOS only. Linux and Windows have not been implemented
or tested.

Put both machine-specific executable paths in the untracked `board/flash.json`:

```json
{
  "cubeide": "/Applications/STM32CubeIDE.app/Contents/MacOS/STM32CubeIDE",
  "programmer": "/path/to/STM32_Programmer_CLI"
}
```

Both entries are required. A different config file can be selected with `--config
PATH`.

## Usage

Close STM32CubeIDE before running the script. From the repository root, run:

```sh
python3 board/flash.py CUBEIDE_PROJECT_DIR
```

For example:

```sh
python3 board/flash.py \
  /Users/asana/NUCLEO-H533RE/ai_can_detection
```

The project directory is the generated CubeIDE project containing `.project` and
`.cproject`. Select its application first with `python3 -m board.prepare`.

The script performs these steps:

1. Read the CubeIDE project name from `.project`.
2. Create a temporary workspace and run a headless clean build of `Debug`.
3. Write the resulting ELF over SWD, verify it and reset the MCU.

CubeIDE and CubeProgrammer output is printed directly in the terminal. The script
does not create log files. A successful build and flash returns exit status 0; a
configuration, project discovery, build or flash failure returns a nonzero status.

## Erasing bank 2 before first use

Flash bank 2 keeps the alarm records. Erase it once over SWD before an application
that writes it first runs on a board. The store reads anything left there as records.

```sh
STM32_Programmer_CLI -c port=SWD -e '[32' '63]'
```

The programmer numbers the sectors of both banks together, so bank 2 is 32 to 63.
Read the option bytes first with `-ob displ`. SWAP_BANK must be 0, or the erase hits
the program.

## Viewing UART output

UART is deliberately separate from the flash command. After flashing, find the
ST-LINK virtual COM port and open it from another terminal when output is needed:

```sh
ls /dev/cu.usbmodem*
screen /dev/cu.usbmodem11202 115200
```

The numeric suffix can change when the board is reconnected. Replace the example
device with the path reported by `ls`. To leave `screen`, press `Ctrl-A`, then `\`.

Automatic UART capture and result detection are deliberately not part of
`board/flash.py`; the hardware smoke test below owns that workflow.

## Hardware smoke test

Run the fixed `model_check_from_flash` smoke test with:

```sh
python3 board/smoke_test.py CUBEIDE_PROJECT_DIR
```

It prepares that application, opens the ST-LINK UART before reset, invokes
`board/flash.py`, and passes when UART reports all 80 rows processed with no dropped
rows or model errors. To replace the smoke application later, edit `APPLICATION` and
`EXPECTED_UART` at the top of `board/smoke_test.py`.

## Unit tests

Command construction and CubeIDE project-name parsing can be tested without a board:

```sh
pytest -q tests/test_flash.py
```
