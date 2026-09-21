# AE reconstruction from Flash

A board application that runs the autoencoder on 80 rows stored in Flash and prints
over UART, for each row, the reconstruction and the reconstruction error as float32
bits and the inference cycles. The rows are the decoded physical values of
`rule_check_from_flash/raw_rows.h`. The application scales them and runs the model in
[`board/lib/active_model/`](../../lib/active_model).

It was made to check two things with that output.

- Whether the board's autoencoder gives the same values as ONNX Runtime on the PC,
  where the threshold was taken.
- How long one row's inference takes.

[compare.py](compare.py) runs the same rows through ONNX Runtime on the PC. It prints
the largest difference of the reconstruction, the largest difference of the
reconstruction error, and the mean and largest cycles.

## Result

Measured on 2026-09-22 with `nonlinear_ae_k8_h64_float` from runs repo
`board/20260916-232708`, against `quantize/20260916-221145/nonlinear_ae_k8_h64_float.onnx`.
The CPU ran at 32 MHz, HSI divided by 2 with no PLL, as set in the CubeIDE project.

| what | result |
|---|---|
| reconstruction, largest absolute difference | 1.49e-6 |
| reconstruction error, largest relative difference | 1.73e-5 |
| inference cycles, mean and largest | 28,796 and 29,066 |
| inference time, mean and largest | 0.90 ms and 0.91 ms |

The board's autoencoder differs from ONNX Runtime by float32 rounding on these rows.
The time covers `model_run` only, not the scaling or the error.

## Requirement

The model in `board/lib/active_model/` must be an autoencoder. The build does not
check this, so any other model with 17 values in and out would print a meaningless
error.

## Limitation

The 80 rows are one stretch of 8 s around one attack in one log, so they cover little
of each signal's range. A match on them does not show a match on rows far from them.
More rows wait until they can be fetched from the dataset instead of the fixed
`raw_rows.h`.

## Run

```sh
python3 -m board.prepare CUBEIDE_PROJECT_DIR ae_reconstruction_from_flash
python3 board/flash.py CUBEIDE_PROJECT_DIR
```

Save the UART output to a file, as in [flash.md](../../docs/flash.md#viewing-uart-output),
until `done: 80 rows`. Then give it the float ONNX file the model was generated from.

```sh
python3 board/application/ae_reconstruction_from_flash/compare.py \
  UART_LOG ONNX_FILE
```
