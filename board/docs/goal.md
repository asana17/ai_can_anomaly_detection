# Board goal

The board application is our entry to the
[TRON Programming Contest 2026](https://www.tron.org/ja/programming_contest-2026/),
RTOS application category, due 2026-09-30 18:00. Judges must be able to run it from
our instructions.

## To do

1. Flash `ai_can_anomaly_detection` and see it start. It builds, and the board was away
   when it was written.
2. The CAN side, as [connecting_can_bus.md](connecting_can_bus.md) describes. Still to
   agree are the clock settings, where the frame timestamp comes from, and whether the
   entry ships with CAN hardware.
3. A status task that reports every second the rows dropped, the frames the FDCAN FIFO
   lost, queue space and CPU use, and blinks the green LED. CPU use needs WFI in
   `low_pow`, which is empty in the STM32 port, and idle time counted with DWT. The
   rules allow changing μT-Kernel 3.0 as long as its API stays, and leave which parts
   of the source to a technical document published separately, not found yet.
4. Measure the time per row of the model the entry runs, reception, rule and report
   latency with inference made heavy, the lowest clock that still meets the 0.1 s tick,
   and the MCU current on JP2 with a tester. Decide whether the entry builds at `-O0`
   as the Debug configuration does, and measure again if not. The row queue depth waits
   for the time per row.
5. Count the calibration rows the board's difference from ONNX Runtime moves across the
   threshold. It waits for the calibration rows' scores from `score`.
6. Fetch the model from the runs repository in `board.prepare`, so the entry's model can
   be changed without editing files. The applications keep the files they have now, so
   a clone builds with nothing fetched. The work is written and set aside, and it waits
   for the new layout's outputs on the Hub.
7. Instructions a judge can follow, slides, the third party software listed (the
   ST Edge AI runtime), and the source published.

## Measured

| what | result | how |
|---|---|---|
| inference time per row | 0.90 ms mean and 0.91 ms largest, 28,796 and 29,066 cycles at 32 MHz | `ae_reconstruction_from_flash`, 80 rows, `nonlinear_ae_k8_h64` float |
| board against ONNX Runtime | largest reconstruction difference 1.49e-6, largest relative error difference 1.73e-5 | the same run and [compare.py](../application/ae_reconstruction_from_flash/compare.py) |
| scoring and detect on Flash rows | alarm from row 1262 to 1313, 60 rows flagged | `scoring_and_detect_from_flash` on the board |
| CAN path on replayed frames | alarm from tick 29 to 80, 60 rows flagged, 89 rows, no errors | `can_path_from_flash` on the board, 2,937 frames |
| reconstruction error in C | bit equal to numpy on 51% of rows, largest relative difference 3.8e-7 | host build of `board/lib/scoring` against the PC scorer |
| generated C renamed by prepare | the same as the C built on the board before, but for the unused `HAVE_NETWORK_INFO` | `board/20260916-232708/nonlinear_ae_k8_h64` |
| image size, the entry | text 84,500, data 2,548, bss 11,828 bytes | `arm-none-eabi-size` of `ai_can_anomaly_detection`, `nonlinear_ae_k16_h128`, Debug at `-O0` |
| image size, the Flash replay | text 123,196, data 2,572, bss 11,580 bytes | `arm-none-eabi-size` of `can_path_from_flash`, 2,937 frames in Flash, Debug at `-O0` |

The image sizes are what `arm-none-eabi-size` prints. Whether the memory the kernel
gives the tasks and message buffers is inside the bss is not checked.

`-ffp-contract=off` is in the CubeIDE build log, so the board's float32 arithmetic
rounds as numpy does. `board/flash.py` builds the project's Debug configuration, which
compiles at `-O0`. The st-ai runtime that runs the layers is a prebuilt library.

The rows and frames of these runs came from the old layout's attack set, attack 2, and
the model's scale and threshold from `results/20260916-001002`.

## Read from the source

`tm_printf` sends each character between `DI` and `EI`, and waits in a loop until the
UART has sent it. The report task therefore keeps the CPU for the whole line, and
every interrupt `DI` masks, the tick and the FDCAN receive interrupt among them, waits
up to one character. That is about 87 µs at 115200 bps, and 174 µs for a line end
with its CR, computed, not measured.
