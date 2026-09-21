# Flash from the command line

`board/flash.py` selects an application, builds the CubeIDE project without opening
the GUI, then writes, verifies and resets the connected board.

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
python3 board/flash.py CUBEIDE_PROJECT_DIR APPLICATION_DIR
```

For example:

```sh
python3 board/flash.py \
  /Users/asana/NUCLEO-H533RE/ai_can_detection \
  board/application/mbf_test
```

The project directory is the generated CubeIDE project containing `.project` and
`.cproject`. The application may be any source directory; it does not have to be below
`board/application`. Its basename selects the library configuration in `board/prepare.py`.

The script performs these steps:

1. Run `board/prepare.py` to select the application and its libraries.
2. Read the CubeIDE project name from `.project`.
3. Create a temporary workspace and run a headless clean build of `Debug`.
4. Write the resulting ELF over SWD, verify it and reset the MCU.

CubeIDE and CubeProgrammer output is printed directly in the terminal. The script
does not create log files. A successful build and flash returns exit status 0; a
prepare, discovery, build or flash failure returns a nonzero status.

## Viewing UART output

UART is deliberately separate from the flash command. After flashing, find the
ST-LINK virtual COM port and open it from another terminal when output is needed:

```sh
ls /dev/cu.usbmodem*
screen /dev/cu.usbmodem11202 115200
```

The numeric suffix can change when the board is reconnected. Replace the example
device with the path reported by `ls`. To leave `screen`, press `Ctrl-A`, then `\`.

Automatic UART capture and Unity result detection are not part of this script. They
can be added later with a separate test-application workflow.

## Unit tests

Command construction, executable discovery and CubeIDE project-name parsing can be
tested without a board:

```sh
pytest -q tests/test_flash.py
```
