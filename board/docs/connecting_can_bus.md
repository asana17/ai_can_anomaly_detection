# Connecting the CAN bus

This page is for whoever brings real CAN frames onto the board.

FDCAN1 is enabled in the CubeMX project, and
[`ai_can_anomaly_detection`](../application/ai_can_anomaly_detection/README.md) starts
it and stores every frame it receives in the slots. It builds. It has not run on the
board. The bus is wired, and [can_bus_debug](../application/can_bus_debug/README.md)
has sent and received frames over it.

```mermaid
flowchart LR
    pc[PC sender] --> usb[USB-CAN adapter] -- CANH, CANL --> tr[CAN transceiver] --> fd["FDCAN1<br/>PB8 RX, PB7 TX"]
    fd -- receive interrupt --> cb["HAL_FDCAN_RxFifo0Callback<br/>slots_store"]
    cb --> slots[(slots)]
    slots --> pre[preprocess, scoring and detect, report]
```

## What is left

| part | what it is | state |
|---|---|---|
| wiring | PB8 and PB7 to an MCP2562FD transceiver, CANH and CANL to the USB-CAN adapter, 120 Ω at both ends of the bus, a common ground | built |
| PC sender | sends frames through the USB-CAN adapter at their own timestamps | none in this repository |
| first run | flash the application and see alarms while the PC sends | not done |

The hardware on hand is a DSD TECH SH-C31A USB-CAN adapter and a Microchip
MCP2562FD-E/P CAN transceiver. Its VDD takes 5 V and its VIO takes the 3.3 V of the
board. [can_bus_debug](../application/can_bus_debug/README.md#wiring) gives its pins.

The adapter runs the candleLight firmware, which Linux drives with its `gs_usb` driver as
a SocketCAN interface. On an Ubuntu PC with `can-utils` installed, this brings it up at
the bus's bit rate and shows every frame:

```sh
sudo ip link set can0 type can bitrate 250000 sample-point 0.875
sudo ip link set can0 up
candump -t d -e can0
```

`cansend can0 18FEF200#1111111111111111` sends one frame.
`ip -details -statistics link show can0` shows the adapter's error counts and bus state.

## FDCAN1 in CubeMX

The settings are in [`board/cubemx/ai_can_detection.ioc`](../cubemx/ai_can_detection.ioc).

| setting | value |
|---|---|
| pins | PB8 RX, PB7 TX |
| frame format | classic CAN, normal mode |
| kernel clock | 32 MHz, PLL1Q from CSI, with N 128 and Q 16. SYSCLK and APB1 stay at 32 MHz from HSI |
| bit timing | prescaler 2, seg1 55, seg2 8, SJW 8, which is 250 kbit/s with the sample point at 87.5% |
| automatic retransmission | on. A frame that loses arbitration or meets an error is sent again |
| filters | none. `can_start` in the application accepts every frame into RX FIFO 0 |
| interrupt | `FDCAN1_IT0_IRQn` at preemption priority 1 |

The recorded bus is SAE J1939, 250 kbit/s, extended 29-bit IDs, as
[can_data.md](../../can_data/can_data.md#source) describes. The bit timing holds only
at a 32 MHz kernel clock. A change to the clock tree changes it.

A kernel clock faster than APB1 loses frames. With the kernel clock at 86 MHz and APB1
at 32 MHz, FDCAN1 acknowledged every frame on the bus but failed to write some of them
into its message RAM. It set the message RAM access failure flag and dropped them. On
2026-09-28 it dropped 11 of 25 frames that way. At 32 MHz it received all 25.

PLL1 runs only for FDCAN. It draws current the board did not draw before, which the
current measurement will include.

## The receive callback

`usermain.c` of the application starts FDCAN1 and holds the callback.

- `can_start` accepts every standard and extended frame into RX FIFO 0, rejects remote
  frames, turns on the new message interrupt and starts FDCAN1. `usermain` calls it
  last, once the tasks and the tick are running.
- `HAL_FDCAN_RxFifo0Callback` empties the FIFO and calls `slots_store` for each frame
  with a 29-bit ID. A DLC above 8 counts as 8 bytes, as classic CAN defines it. The
  receive time is the DWT cycle counter, which `model_init` turns on. Nothing reads the
  time yet.

RX FIFO 0 holds 3 frames, `SRAMCAN_RF0_NBR` in the H5 HAL. Frames it loses are not
counted yet.

## Interrupt priority

Preprocessing copies the slots one at a time between `DI` and `EI`, so the receive
interrupt never meets a half written slot. That holds only if `DI` masks the FDCAN
interrupt.

In the STM32H5 port `DI` raises BASEPRI to `INTPRI_MAX_EXTINT_PRI`, which is 1 in
`mtk3_bsp2/include/sys/sysdepend/stm32_cube/cpu/stm32h5/sysdef.h`. `DI` therefore masks
interrupts of priority 1 to 15 and leaves priority 0 running. `FDCAN1_IT0_IRQn` is at 1.
This is read from the port's source and not yet checked on the board.

`tm_printf` masks the same interrupts while it sends each character, about 87 µs at
115200 bps, and 174 µs for a line end, computed, not measured. A classic frame with
8 bytes takes about 0.5 ms at 250 kbit/s, so the FIFO holds what arrives meanwhile.

## Fetching the frames to send

The frames for the PC to send are in a test set of the dataset repository on Hugging
Face, `asana17/ai_can_anomaly_detection_data`, which needs no login. A test set holds
its logs with the attacks injected, frame by frame, as Parquet files under `frames/`,
and which attack each log holds in `injected.json`. Their columns are in
[injected_frames](../../assemble/docs/injected_frames.md).

The CAN logs themselves, normal traffic with no attack, come from the Turku dataset as
[can_data.md](../../can_data/can_data.md#getting-it) describes.

## Checking it

Prepare, build and flash, then read the UART on the ST-LINK virtual COM port while the
PC sends. [setup.md](setup.md) and [flash.md](flash.md) give the steps.

```sh
python3 -m board.prepare CUBEIDE_PROJECT_DIR ai_can_anomaly_detection
python3 board/flash.py CUBEIDE_PROJECT_DIR
```

The first line names the model and says FDCAN1 is being read. `FDCAN start error` in
its place means FDCAN1 did not start. An alarm line appears only when a replayed
attack reaches rows above `MIN_SPEED`.
