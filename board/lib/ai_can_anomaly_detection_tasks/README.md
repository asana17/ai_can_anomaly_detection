# ai_can_anomaly_detection_tasks

The tasks that turn the slots into alarms. ai_can_anomaly_detection and
can_path_from_flash both run them. They differ in what fills the slots and in the task
that reports the alarms, which the application makes.

| application | reports with | priority |
|---|---|---|
| ai_can_anomaly_detection | [report_can](../report_can), one frame on FDCAN1 | 9 |
| can_path_from_flash | [report_uart](../report_uart), one line over UART | 9 |

```mermaid
flowchart LR
    slots[(slots)] --> pre["preprocess 6<br/>row from the slots, above MIN_SPEED"]
    tick[cyclic handler 0.1 s] -. wakes .-> pre
    pre -- row queue --> sd["score and detect by row 8<br/>rules, autoencoder, k of the last N"]
    sd -- latest report --> report["report 9<br/>CAN or UART"]
    sd -- latest positions --> copy["copy alarm frames 10<br/>frames behind alarm A"]
    frames[(frame ring)] --> copy
    copy -- latest alarm frames --> store["the application's store"]
    sd -- shared ring --> win["score and detect by window 11<br/>window model on the last rows"]
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
hold a model large enough. The window model is the one there. It runs on the time the
guaranteed layer leaves and skips its inference when there is none. A skip loses only
the detections that model alone makes.

Filling the window belongs to the guaranteed layer. A row dropped before it enters the
buffer leaves a gap, and the model then scores a stretch of time that never happened.

Report sits below both guaranteed tasks and above the copy of the alarm frames. The
copy sits above the windowed model, since the frame ring overwrites the frames it has
not copied.

Score and detect by row hands report only the latest alarm state, as the CAN receive
interrupt hands preprocessing the slots. A new state goes over the one before. So
writing never waits for report, and report always gets the current state.

## Copying the frames behind alarm A

On each tick preprocess reads the frame ring's position once, and gives the row the
positions at the tick before and at its own. So each row names the frames that arrived
since the tick before.

When alarm A starts, score and detect by row passes the row it starts on and the
positions of the frames behind the rows that raised it. Those are the last
`DETECT_BY_ROW_RECENT_FLAGS` rows, or fewer since the last gap. As with report, only
the latest positions are kept.

The copy takes the latest `ALARM_FRAMES_MAX` of those frames, oldest first, without
stopping interrupts. It then reads the ring's position again. When newer frames went
over any of those it copied, it keeps none, and the record holds only the row. It hands
the alarm frames on, again keeping only the latest. Their record is in
[store_alarm_frames_input.h](../store_alarm_frames/store_alarm_frames_input.h).

## Passing rows

Score and detect by row puts each row in a shared ring, with whether the row was
flagged and the row's place since the last gap, 0 for the first row after it.

Score and detect by window first copies every row in the shared ring at once, and the
shared ring is emptied. It may hold several rows, since score and detect by window has
a lower priority. The task then adds the copied rows to its window one at a time. After
each row, it checks whether the window is complete, and if so scores it.

## Scoring a window

The window is `WINDOW_MODEL_ROWS` rows, and one is scored every `WINDOW_MODEL_STRIDE`
rows. Each row is z-scored with the scale of the window model's own fit, the model runs
on the window, and the score is the mean squared error on its last row, as on the PC.
Nothing reads the score.
