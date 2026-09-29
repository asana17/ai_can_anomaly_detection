# Window model check from Flash

A board application that runs the window model on every window of `WINDOW_MODEL_ROWS`
rows it can make from the 80 rows of `rule_check_from_flash/raw_rows.h`. It prints
over UART, for each window, the score as float32 bits and the inference cycles, and at
the end the fewest and most cycles. The rows are z-scored with the scale of the window
model's fit and the score is the mean squared error on the window's last row, as in
`score_and_detect_by_window`.

It was made to check two things.

- Whether the board's window model and score give the same values as ONNX Runtime on
  the PC.
- How long one window's inference takes, which sets `WINDOW_MODEL_STRIDE`.

[compare.py](compare.py) scores the same windows with ONNX Runtime and the ONNX file in
[`board/lib/deployed_window_model/`](../../lib/deployed_window_model). It prints the
largest difference of the score, and the mean and largest cycles.

## Result

Measured on 2026-09-29 with `window_conv1d_ae_r50_s3_k16_h64` in int8, from runs repo
`window_board/20260929-113106`, against its `window_model.onnx`. The Release build ran
at `-O2` and 32 MHz.

| what | result |
|---|---|
| windows | 31, ending at rows 1292 to 1322 |
| score on the PC | 0.2760 to 24.0516 |
| score, largest absolute difference | 1.91e-6 |
| inference cycles, mean and largest | 2,721,689 and 2,721,816 |
| inference time, largest | 85.1 ms |

The time covers the st-ai inference inside `window_model_run` only, not the int8
conversion of the input and output, the scaling or the score.

## Limitation

The 80 rows are one stretch of 8 s around one attack in one log, as for
[ae_reconstruction_from_flash](../ae_reconstruction_from_flash/README.md).

## Run

```sh
python3 -m board.prepare window_model_check_from_flash
python3 -m board.flash
```

Save the UART output to a file, as in [flash.md](../../docs/flash.md#viewing-uart-output),
until `done: 61 windows`. Then compare it.

```sh
python3 board/application/window_model_check_from_flash/compare.py UART_LOG
```
