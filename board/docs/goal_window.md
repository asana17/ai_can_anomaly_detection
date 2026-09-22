# Board goal with a windowed model

How the board application grows from the instant model to a windowed one. The
windowed model reads a stretch of rows and costs more time than the board can promise
every tick, so it runs below the tasks that raise the instant alarm, at a lower rate
than the instant model, and lower still when the CPU is short. Nothing here is built yet.

## Frames and rows

The FDCAN receive interrupt stays as it is. `slots_store` overwrites the slot of the
frame's PGN and returns, so a frame is never lost to work done after it. Everything
that reads more than one moment works on the 0.1 s rows the preprocess task builds
from the slots, never on frames.

A rule that compares a signal with its previous value, like `change_limit`, compares
a row with the row before it. The time between them is the tick, 0.1 s, rather than
the gap between two frames, so a burst of frames cannot shrink it. Its limits are
measured on rows, since a row folds several frames into one step and moves slower
than a frame does.

Whether rules that read over time run on rows or on frames is not settled. Rows are
the plan above. The two compare as follows.

| | on frames | on rows |
|---|---|---|
| what it sees | every frame, as often as it is sent, 20 ms for EEC1. A frame slipped in between ticks and overwritten before the next one is seen | the last frame of each PGN at each tick. A frame overwritten before the tick is seen by neither the rules nor the models |
| where it runs on the board | inside the receive interrupt, or in a task fed by a frame queue added for it | in a task after the row is built, with the interrupt unchanged |
| cost | grows with the frames on the bus | fixed per tick |
| time between two readings | the gap between two frames of the PGN, which the truck holds to its period. No pair of frames arrives early, so a burst is not what inflates the rate | 0.1 s. The frames behind two rows are not 0.1 s apart, and a PGN sent every 100 ms can update 0 or 2 times between ticks, showing a rate of 0 or double. Not measured |
| limits | the current `LIMITS`, measured between frames | measured on rows, and far tighter |
| against the models | sees finer time than the models, which read rows, so as a floor it is not level with them | reads the same rows as the models |
| joining the row flags | needs each hit turned into whether one fell since the last tick | the hit is already a row flag |
| delay | the frame's arrival | up to one tick |

Both were measured on the non-test logs, and are written up in
[attack/measurements.md](../../attack/measurements.md).

The frames arrive on their period. Over 200 logs read frame by frame, not one pair of
frames of a PGN arrives inside half its usual gap, and the fastest jumps are measured
over an ordinary gap. So the tail of the frame limits is the signal moving, or a bad
reading, and not a burst dividing by a short gap.

A row is the tighter step of the two. Over 2,062,116 steps of the non-test logs, taken
between two moving rows one tick apart, a signal moves this far.

| signal | 1e-3 | 1e-4 | 1e-5 | most | the frame limit now |
|---|---|---|---|---|---|
| wheel_speed | 14.0 | 21.0 | 37.8 | 300 | 50.0 |
| tachograph_speed | 14.0 | 21.0 | 33.0 | 171 | 100.0 |
| steering_angle | 5.16 | 7.29 | 9.53 | 11.1 | 40.0 |
| yaw_rate | 0.21 | 0.28 | 0.37 | 0.49 | 3.0 |

yaw_rate never moves further than 0.49 rad/s2 in a row, against a frame limit of 3.0.
Signals the frame rule could not bound come out bounded on a row, engine_speed at 2,825
rpm/s, actual_engine_torque at 490 and brake_pedal at 360. input_shaft_speed,
clutch_slip and the gears still move their whole range in one row, so no limit fits
them either way.

What the move does not buy is detection. On an attacked test set the rule fires as
often somewhere else in the log as on the attack itself, at every limit, so it belongs
below the models as a floor and not as a detector of its own.

## Windows

A window is the last W rows. The ring that holds them is emptied whenever a row
number is not one more than the one before, which happens on a quiet tick, a tick
before every PGN has arrived, a tick below the moving speed, and a row dropped from
the queue. A window therefore never spans a gap, and the PC cuts its windows by the
same rule, over moving rows one tick apart inside a grid segment.

The first W − 1 rows of every run get no window, and neither does a run shorter than
W. Those rows are left to the rules and the instant model. Over grid
`20260922-093129` the share of moving rows a window covers is this.

| W | rows | moving rows covered | runs shorter than W |
|---|---|---|---|
| 10 | 1 s | 97.6% | 11.3% |
| 20 | 2 s | 95.1% | 15.3% |
| 50 | 5 s | 88.1% | 21.5% |

A window of 50 rows of 17 floats is 3.4 KB.

## Tasks

```mermaid
flowchart LR
    irq["FDCAN1 receive callback"] -- slots_store --> slots[(slots)]
    tick[cyclic handler 0.1 s] -. wakes .-> pre
    slots --> pre["preprocess 6<br/>row from the slots"]
    pre -- row queue --> sd["scoring and detect 8<br/>rules, instant model, alarm A<br/>fills the window ring"]
    sd -- latest window --> win["window 11<br/>windowed model every S rows, alarm B"]
    sd -- report queue --> report["report 10<br/>UART"]
    win -- report queue --> report
```

The numbers are task priorities, smaller runs first.

| task | what it does | when it falls behind |
|---|---|---|
| preprocess | builds a row every tick and numbers it | the row queue drops its oldest row |
| scoring and detect | runs the rules and the instant model on every row, raises alarm A, adds the row to the ring, hands the latest window over | must not happen, it is sized to finish inside a tick |
| report | prints over UART | lines wait, nothing is lost |
| window | runs the windowed model on the window it was handed, raises alarm B | windows in between are skipped |

Scoring and detect fills the ring rather than the window task, because a row the
window task misses would leave a gap inside the window and the model would score a
stretch of time that never happened.

Report sits above the window task so that alarm A is printed without waiting for an
inference.

## The window task

The windowed model runs at a lower rate than the instant model. The instant model
scores every row, once every 0.1 s. The windowed model scores one window every S
rows, once every S × 0.1 s. A window already holds W rows of history, so scoring it
on every row repeats most of the work of the row before. With S no larger than W every
row still falls in some window, and alarm B comes up to S rows late.

The CPU runs at 32 MHz from HSI, and the interrupt handlers run on it at that clock.
The 86 MHz from PLL1Q drives only the FDCAN peripheral. The instant model took 28,796
cycles for about 3,200 multiply accumulates at `-O0`, about 9 cycles each. Scaling
that to a windowed autoencoder with 128 hidden units and a code of 16 gives the times
below, an estimate and not a measurement.

| W | multiply accumulates | time at 32 MHz |
|---|---|---|
| 10 | about 48k | about 13 ms |
| 50 | about 223k | about 63 ms |

At W = 50 one inference takes more than half the tick, so the model cannot run on
every row at this clock.

S is taken from the model's time measured on the board, as the smallest S whose
average load leaves room in the tick. It is counted from the W-th row after the ring
was emptied. The rule is fixed, so the PC picks the same rows and the board's alarm B
can be compared with the PC's.

Under heavier load the rate drops further on its own. When the window task is still
busy as a new window is handed over, the new one replaces the waiting one, so the task
never runs more than one inference behind and the windows in between go unscored.

The handover buffer is written by scoring and detect while the window task may be
copying it. Either dispatch is disabled for the copy with `tk_dis_dsp`, or two buffers
are swapped.

## Two alarms

Alarm A is the rules OR the instant model, row by row, then `HOLD`. It is raised on
time every tick.

Alarm B is the rules and instant flag of the row the window ends on, OR the windowed
model's flag, then a hold counted over the windows the task ran. It comes late and may
skip windows under load.

## Load to show the priorities working

The entry should show alarm A staying on time while load pushes the window task to a
wider stride and then to skipped windows. Work an ECU commonly carries serves as that
load.

| work | what it does | how it loads the CPU |
|---|---|---|
| event recorder | writes the frames or rows around an alarm to Flash | Flash erase and write are slow and come in bursts |
| SecOC | checks a MAC, such as AES-CMAC, on each frame | grows with the bus load. Whether the H533's AES hardware can do it is not checked |
| J1939 diagnostics | reassembles TP.CM and TP.DT and reads DM1 fault codes | light but always present |
| gateway | forwards filtered frames to FDCAN2 | has its own deadline, so it would sit above detection |
| self check | computes a CRC over Flash on a period | heavy and periodic, and can wait |

## Open

- The windowed model's time per window on the board at 32 MHz, which sets S.
- How alarm B holds across skipped windows.
- Whether the handover uses `tk_dis_dsp` or two buffers, and how long the copy takes.
- Which load the entry carries.
