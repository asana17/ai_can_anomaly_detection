# alive

Blinks the green LED and prints a count over UART every 500 ms. It is the first
application to flash, to see that flashing and the UART work.

## Check on the board

```sh
python3 -m board.prepare CUBEIDE_PROJECT_DIR alive
python3 board/flash.py CUBEIDE_PROJECT_DIR
```

Read the UART as in [flash.md](../../docs/flash.md#viewing-uart-output). Expected:

```
usermain 1
usermain 2
```

and so on every 500 ms, with the green LED blinking.
