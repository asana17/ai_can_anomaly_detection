# can_bus_debug

Prints every frame FDCAN1 receives over UART, and sends one frame with ID `0x18FEF100`
every second. It was made to check that frames go both ways between the board and the
CAN bus. FDCAN1 is on PB8 for receiving and PB7 for sending.

## Wiring

The CAN transceiver is a Microchip MCP2562FD-E/P, an 8 pin DIP. Its VDD takes 4.5 V to
5.5 V, and VIO sets the logic level to the 3.3 V of the board. STBY is held low, since
high puts the transceiver in standby, where it does not send.

| MCP2562FD pin | goes to |
|---|---|
| 1 TXD | CN10 pin 5, PB7 |
| 2 VSS | GND, CN7 pin 20 |
| 3 VDD | CN7 pin 18, 5V |
| 4 RXD | CN10 pin 36, PB8 |
| 5 VIO | CN7 pin 16, 3V3 |
| 6 CANL | CANL of the USB-CAN adapter |
| 7 CANH | CANH of the USB-CAN adapter |
| 8 STBY | GND |

CN7 and CN10 are the ST morpho connectors of the NUCLEO-H533RE, as Table 17 of UM3121
gives them. The ground of the USB-CAN adapter joins the same GND.

## Check on the board

It needs the CAN bus that [connecting_can_bus.md](../../docs/connecting_can_bus.md)
describes, with the USB-CAN adapter on a PC.

```sh
python3 -m board.prepare can_bus_debug
python3 -m board.flash
```

On macOS `python3 -m board.application.can_bus_debug.bus` sends one frame and prints the
frames on the bus. On Ubuntu `cansend` and `candump` do the same.

The UART should show `CAN TX: ID=0x18fef100 queued` every second, and the adapter
should receive that frame. For each frame the adapter sends, the UART should show a
line that starts with `CAN RX:` and holds the frame's ID and data.

`FDCAN start error` means FDCAN1 did not start. `send failed` means the board could
not queue the frame for sending.

Every second the UART also shows where the frames FDCAN1 received went:

```
CAN RX status: taken 25, printed 25, fifo 0, fifo lost 0, ram failed 0, rec 0, tec 0
```

| field | what it is |
|---|---|
| `taken` | frames the receive interrupt took from RX FIFO 0 since reset |
| `printed` | of those, frames already printed as `CAN RX:` lines |
| `fifo` | frames waiting in RX FIFO 0 now |
| `fifo lost` | 1 when a frame was dropped because RX FIFO 0 was full, since the last line |
| `ram failed` | 1 when FDCAN1 dropped a frame it could not write into its message RAM, since the last line |
| `rec`, `tec` | the receive and transmit error counters of FDCAN1 |

On a working bus `taken` counts every frame sent to the board, `printed` catches up
with it, and the rest stay 0.
