# Board goal

The board application is our entry to the
[TRON Programming Contest 2026](https://www.tron.org/ja/programming_contest-2026/),
RTOS application category, due 2026-09-30 18:00. Judges must be able to run it from
our instructions.

## To do

1. Put the new layout's outputs on the Hub, the test set, `models/`, `thresholds/`,
   `onnx/` and `board/`, and fill the nulls in [`board/model.json`](../model.json).
   Until then no application with a model, rows or frames can be prepared.
2. Prepare, build and flash every application from the fetched files, and run the
   smoke test.
3. Count the calibration rows the board's difference from ONNX Runtime moves across
   the threshold. It waits for the calibration rows' scores from `score`.
4. A status task that reports every second the rows dropped, the frames the FDCAN FIFO
   lost, queue space and CPU use, and blinks the green LED. CPU use needs WFI in
   `low_pow`, which is empty in the STM32 port, and idle time counted with DWT. Whether
   the contest allows changing `low_pow` is open.
5. Measure reception, rule and report latency with inference made heavy, the lowest
   clock that still meets the 0.1 s tick, the MCU current on JP2 with a tester, and
   `arm-none-eabi-size` of the whole image. The row queue depth waits for the time per
   row.
6. The `can_path` application on the real bus, with the CAN side, as
   [connecting_can_bus.md](connecting_can_bus.md) describes. Still to agree with the
   CAN side are the clock settings, where the frame timestamp comes from, and whether
   the entry ships with CAN hardware.
7. Instructions a judge can follow, slides, the third party software listed (the
   ST Edge AI runtime), and the source published.

Whether `tm_printf` spins while UART sends is not known.

## Measured

| what | result | how |
|---|---|---|
| inference time per row | 0.90 ms mean and 0.91 ms largest, 28,796 and 29,066 cycles at 32 MHz | `ae_reconstruction_from_flash`, 80 rows, `nonlinear_ae_k8_h64` float |
| board against ONNX Runtime | largest reconstruction difference 1.49e-6, largest relative error difference 1.73e-5 | the same run and [compare.py](../application/ae_reconstruction_from_flash/compare.py) |
| scoring and detect on Flash rows | alarm from row 1262 to 1313, 60 rows flagged | `scoring_and_detect_from_flash` on the board |
| CAN path on replayed frames | alarm from tick 29 to 80, 60 rows flagged, 89 rows, no errors | `can_path_from_flash` on the board, 2,937 frames |
| reconstruction error in C | bit equal to numpy on 51% of rows, largest relative difference 3.8e-7 | host build of `board/lib/scoring` against the PC scorer |
| generated C renamed by prepare | the same as the C built on the board before, but for the unused `HAVE_NETWORK_INFO` | `board/20260916-232708/nonlinear_ae_k8_h64` |

`-ffp-contract=off` is in the CubeIDE build log, so the board's float32 arithmetic
rounds as numpy does.

The rows and frames of these runs came from the old layout's attack set, attack 2, and
the model's scale and threshold from `results/20260916-001002`.
