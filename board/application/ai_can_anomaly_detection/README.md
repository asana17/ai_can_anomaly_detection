# ai_can_anomaly_detection

The application the entry runs. It builds a row from the slots every 0.1 s, scores it
with the rules and the autoencoder, and reports each alarm over UART.

FDCAN1 receives the frames, and its receive callback stores each one in the slots with
`slots_store`. The application builds. It has not run on the board, and no frame has
reached it, since the bus is not wired.
[connecting_can_bus.md](../../docs/connecting_can_bus.md) has the FDCAN settings and
what is left.

```mermaid
flowchart LR
    irq["FDCAN1 receive callback"] -- slots_store --> slots[(slots)]
    slots --> tasks["the tasks in board/lib/ai_can_anomaly_detection_tasks"]
```

The tasks after the slots are described in
[their README](../../lib/ai_can_anomaly_detection_tasks/README.md). The application runs
until the board is reset.

## The model

It runs `nonlinear_ae_k16_h128`, the largest model of the export in
[`board/lib/deployed_model/`](../../lib/deployed_model), with the scale of the fit it
came from and the threshold `calibrate` took for it. The sample applications run a
smaller one from `board/lib/active_model/`, so changing one leaves the other alone.

The files come from the runs repository, `board/20260916-232708/nonlinear_ae_k16_h128/`
and `results/20260916-001002`. They are kept here so that the application builds from a
clone with nothing fetched.

## Prepare, build and flash

```sh
python3 -m board.prepare CUBEIDE_PROJECT_DIR ai_can_anomaly_detection
python3 board/flash.py CUBEIDE_PROJECT_DIR
```

## Size

`arm-none-eabi-size` of the image, built on 2026-09-22 in the Debug configuration,
which compiles at `-O0`.

| what | bytes |
|---|---|
| text | 93,972 |
| data | 2,548 |
| bss | 11,932 |
