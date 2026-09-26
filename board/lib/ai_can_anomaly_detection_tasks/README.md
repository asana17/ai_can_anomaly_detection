# ai_can_anomaly_detection_tasks

The tasks that turn the slots into alarms. ai_can_anomaly_detection and
can_path_from_flash both run them, and differ only in what fills the slots.

```mermaid
flowchart LR
    slots[(slots)] --> pre["preprocess 6<br/>row from the slots, above MIN_SPEED"]
    tick[cyclic handler 0.1 s] -. wakes .-> pre
    pre -- row queue --> sd["scoring and detect 8<br/>rules, scale, autoencoder, threshold, k of the last N"]
    sd -- report queue --> report["report 10<br/>UART"]
```

The numbers are task priorities, smaller runs first.

## Preprocessing

On each tick preprocessing copies the slots into a row. It sends the row on when a
frame has arrived since the last tick, every PGN has arrived, and the wheel speed is
above `MIN_SPEED`. The row number counts ticks, so a row it does not send leaves a gap
and the alarm count restarts there. After 1 s with no frame it clears the slots, as
`grid_sample` does across a gap.

A tick with no new frame sends no row, since the row would hold only old values. The
PC holds them across a gap up to 1 s, so there the board sends fewer rows. A J1939 bus
goes 0.1 s without a frame only when it or its senders stop.

## Priorities

A task sits in one of two layers, and the layer sets its priority.

The guaranteed layer holds the rules and the instant model. A row built in one tick is
scored and its alarm raised before the next tick. Nothing in it is dropped. The board
can promise this, with 0.90 ms of inference against a 0.1 s tick.

The best-effort layer holds detection the board cannot promise, since an ECU cannot
hold a model large enough. A windowed model is the one planned. It runs on the time the
guaranteed layer leaves and skips its inference when there is none. A skip loses only
the detections that model alone makes.

Filling the window belongs to the guaranteed layer. A row dropped before it enters the
buffer leaves a gap, and the model then scores a stretch of time that never happened.

Report is best effort by the same rule, since a late line loses nothing. It sits below
both guaranteed tasks.
