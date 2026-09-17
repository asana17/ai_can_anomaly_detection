# preprocess_c

C port of [`preprocess/`](../preprocess) for the NUCLEO-H533RE (STM32H533,
Cortex-M33). Reads raw J1939/FMS CAN frames and produces a 17-signal `float`
row every 100 ms — the input the anomaly-detection model expects — entirely in
firmware, with no Python on the board.

---

## 1. What was done

### 1.1 What was ported

The Python `preprocess/` module has two sub-pipelines. Only the **inference-time
path** is ported; CSV loading and profiling tools stay on the PC.

| C file | Replaces | What it does |
|---|---|---|
| `can_id.h / .c` | `frames/can_id_decompose.py` | Decompose a 29-bit J1939 arbitration ID → `(priority, pgn, source_address)` |
| `spn_decode.h / .c` | `frames/spn_decode.py` | Extract a SPN bit-field from a payload → physical `float`; returns `NAN` for J1939 not-available/error markers |
| `spn_spec.h / .c` | `frames/spn_spec.py` | Compile-time decode table: 9 PGNs, 17 signals, with scale/offset/range |
| `frame_decode.h` | `frames/frame_decode.py` | Inline: decode all SPNs of one PGN in a single call |
| `signal_state.h / .c` | `features/signal_state.py` | Hold-last buffer for 17 signals; `NAN` until first frame of each signal arrives |
| `grid_sample.h / .c` | `features/grid_sample.py` | Event-driven 100 ms grid resampler; calls a callback whenever a complete row is ready |
| `preprocess.h` | — | Single umbrella header; firmware only needs this one `#include` |

**Not ported** (PC-side only):

| Python module | Reason |
|---|---|
| `frames/can_log_loader.py` | On the board, frames come directly from the CAN hardware peripheral (FDCAN). There is no CSV file to read. The loader only exists to replay recorded logs on a PC. |
| `preprocess/profile/` | These are data analysis tools (PGN counts, intervals, classify) used to measure and explore the dataset offline. They are not part of the real-time inference pipeline. |

### 1.2 What was built for testing

| File | Purpose |
|---|---|
| `test/Makefile` + 4 test files | Native C unit tests (standalone, no Python needed) |
| `Makefile` | Builds `libpreprocess.dylib` / `.so` shared library |
| `bindings.py` | Python `ctypes` bridge — lets Python call the compiled C functions directly |
| `tests/test_c_differential.py` | `pytest` test suite that runs **both** Python and C on the same inputs and asserts equivalence |
| `compare/gen_golden.py` | Generates Python "golden reference" output for a synthetic CAN stream |
| `compare/compare.c` | Runs the same synthetic stream through the C pipeline |
| `compare/verify.py` | Compares the two text outputs signal-by-signal |
| `compare/run_compare.sh` | One-command script that compiles, runs both, and verifies |

---

## 2. How to use it / walkthrough

### 2.1 Using it in firmware

Include the single umbrella header and create one `GridSampler` instance.
Feed every CAN frame you receive — in any order, from any ISR or task — by
calling `grid_feed()`.  When the grid has accumulated enough data to fill a
complete 100 ms row, it calls your `on_row` callback synchronously.

```c
#include "preprocess.h"

static GridSampler g_sampler;

/* Called by grid_feed() once every 100 ms of valid CAN traffic. */
static void on_row(const float row[NUM_SIGNALS], uint32_t tick_ms)
{
    /* row[0..16] is ready — pass it to the anomaly-detection model. */
    model_infer(row);
}

/* Call once at startup. */
void app_init(void)
{
    /* period_ms = 100 (10 Hz grid), max_hold_ms = 1000 (reset after 1 s gap). */
    grid_sampler_init(&g_sampler, 100, 1000, on_row);
}

/* Call from the STM32 FDCAN RX interrupt or RTOS receive task. */
void on_can_frame_received(uint32_t arb_id, uint8_t *data, uint8_t dlc)
{
    grid_feed(&g_sampler, arb_id, data, dlc, HAL_GetTick());
}
```

### 2.2 Running the tests

There are **three layers** of testing, each serving a different purpose:

#### Layer 1: Native C unit tests (no Python needed)

Tests the C code in isolation using hand-written assertions in pure C.

```bash
cd preprocess_c/test
make test
```

Result: 4 test binaries, ~20 checks — verifies CAN ID parsing, SPN decoding, signal state logic, and grid resampling individually.

#### Layer 2: Python vs. C differential tests (pytest + ctypes)

**This is the main comparison tool.** It compiles the C code into a shared library (`libpreprocess.dylib`), loads it into Python via `ctypes`, then feeds identical inputs through both the Python and C implementations and asserts the outputs match.

```bash
# First time: build the shared library
make -C preprocess_c

# Run the differential tests
pytest tests/test_c_differential.py -v
```

What gets compared (18 test cases):

| Test | What it checks |
|---|---|
| `test_diff_can_id_decompose` × 13 IDs | Priority, PGN, Source Address for PDU1, PDU2, extended, masked, broadcast IDs |
| `test_diff_spn_decode_all_specs` | All 17 SPNs × 5 payload patterns = 85 decode comparisons |
| `test_diff_spn_decode_unavailable_and_error` | All 17 SPNs with `0xFF` (NA) and `0xFE` (error) bytes |
| `test_diff_signal_state_lifecycle` | Init → partial updates → ready check → row extraction |
| `test_diff_resample_golden_stream` | Full end-to-end: 11 CAN frames → 2 emitted rows, all 17 signals |
| `test_diff_resample_gap_reset` | 1.0 s gap detection and state reset behavior |

Each comparison asserts: `|python_value - c_value| < 1e-4`.

#### Layer 3: Standalone golden output comparison (CLI)

A simpler approach that runs both pipelines as separate processes and diffs the text output.

```bash
cd preprocess_c/compare
./run_compare.sh
```

#### Running all layers at once

```bash
make -C preprocess_c test
```

This runs Layer 1 (native C tests) then Layer 2 (differential pytest) in one command.

### 2.3 Signal order

The 17-element `float row[]` produced by the grid sampler uses the same column
order as the Python `SIGNALS` list. Models trained on the PC expect this exact
layout.

| Index | Signal | PGN | Unit |
|---|---|---|---|
| 0 | `engine_speed` | EEC1 (61444) | rpm |
| 1 | `driver_demand_torque` | EEC1 | % |
| 2 | `actual_engine_torque` | EEC1 | % |
| 3 | `accel_pedal` | EEC2 (61443) | % |
| 4 | `engine_load` | EEC2 | % |
| 5 | `wheel_speed` | CCVS1 (65265) | km/h |
| 6 | `fuel_rate` | LFE1 (65266) | L/h |
| 7 | `output_shaft_speed` | ETC1 (61442) | rpm |
| 8 | `clutch_slip` | ETC1 | % |
| 9 | `input_shaft_speed` | ETC1 | rpm |
| 10 | `selected_gear` | ETC2 (61445) | gear |
| 11 | `current_gear` | ETC2 | gear |
| 12 | `tachograph_speed` | TCO1 (65132) | km/h |
| 13 | `brake_pedal` | EBC1 (61441) | % |
| 14 | `steering_angle` | VDC2 (61449) | rad |
| 15 | `yaw_rate` | VDC2 | rad/s |
| 16 | `lateral_accel` | VDC2 | m/s² |

---

## 3. Test results summary

### Differential test results (Python vs. C)

```
tests/test_c_differential.py::test_diff_can_id_decompose[...] PASSED  (×13)
tests/test_c_differential.py::test_diff_spn_decode_all_specs PASSED
tests/test_c_differential.py::test_diff_spn_decode_unavailable_and_error PASSED
tests/test_c_differential.py::test_diff_signal_state_lifecycle PASSED
tests/test_c_differential.py::test_diff_resample_golden_stream PASSED
tests/test_c_differential.py::test_diff_resample_gap_reset PASSED

18 passed in 0.02s
```

### Per-signal accuracy

| Signal | Max |Python − C| | Status |
|---|---|---|
| `engine_speed` | 0.00e+00 | EXACT |
| `driver_demand_torque` | 0.00e+00 | EXACT |
| `actual_engine_torque` | 0.00e+00 | EXACT |
| `accel_pedal` | 0.00e+00 | EXACT |
| `engine_load` | 0.00e+00 | EXACT |
| `wheel_speed` | 0.00e+00 | EXACT |
| `fuel_rate` | 0.00e+00 | EXACT |
| `output_shaft_speed` | 0.00e+00 | EXACT |
| `clutch_slip` | 0.00e+00 | EXACT |
| `input_shaft_speed` | 0.00e+00 | EXACT |
| `selected_gear` | 0.00e+00 | EXACT |
| `current_gear` | 0.00e+00 | EXACT |
| `tachograph_speed` | 0.00e+00 | EXACT |
| `brake_pedal` | 0.00e+00 | EXACT |
| `steering_angle` | 1.00e-06 | PASS |
| `yaw_rate` | 0.00e+00 | EXACT |
| `lateral_accel` | 0.00e+00 | EXACT |

16/17 signals are bit-identical. The 1e-6 difference on `steering_angle` is
expected: Python uses 64-bit `float` (double), C uses 32-bit `float` to match
the hardware FPU and ONNX model dtype. The literal `-31.374` rounds differently
in 32 vs 64 bits. This is well within the 1e-4 tolerance.

---

## 4. Next steps

- [ ] **Cross-compile verification** — build with `arm-none-eabi-gcc` for
      Cortex-M33 and confirm zero warnings, then check the `.map` file for
      flash/RAM usage.
- [ ] **On-board golden test** — hard-code a short sequence of real CAN frames
      (e.g. the first 200 frames from one log) into firmware flash.  Call
      `grid_feed()` for each, collect rows over UART, and compare them
      byte-for-byte against the Python `resample()` output on the same frames.
- [ ] **FDCAN HAL integration** — replace the test stub with a call from the
      STM32 `HAL_FDCAN_RxFifo0Callback` or equivalent RTOS task.
- [ ] **Port the rules layer** — `rules/instant/` (9 stateless checks) and
      `rules/rate/` (1 rate-of-change check) are the natural next C port.
      They operate on the same `float row[17]` that `grid_sample` produces.
- [ ] **End-to-end smoke test** — run the full pipeline (preprocessing → rules
      → model inference) on the board with live CAN traffic and compare scores
      against the PC ONNX Runtime output.

---

## 5. Notes

### File structure

```
preprocess_c/
├── Makefile                 # Builds libpreprocess shared library
├── preprocess.h             # Single umbrella header for firmware
├── can_id.h / .c            # CAN ID decomposition
├── spn_decode.h / .c        # SPN bit-field extraction
├── spn_spec.h / .c          # Static decode table (9 PGNs, 17 signals)
├── frame_decode.h           # Inline: decode all SPNs of one frame
├── signal_state.h / .c      # Hold-last signal buffer
├── grid_sample.h / .c       # Event-driven grid resampler
├── bindings.py              # Python ctypes bridge to libpreprocess
├── libpreprocess.dylib      # Compiled shared library (macOS)
├── test/
│   ├── Makefile             # Builds native C test binaries
│   ├── test_can_id.c
│   ├── test_spn_decode.c
│   ├── test_signal_state.c
│   └── test_grid_sample.c
└── compare/
    ├── Makefile             # Builds standalone C comparison binary
    ├── gen_golden.py        # Python golden reference generator
    ├── compare.c            # C equivalent of gen_golden.py
    ├── verify.py            # Signal-by-signal numerical comparator
    └── run_compare.sh       # One-command build + run + verify
```

### Cross-compiling for the board

The library has no external dependencies (only `<stdint.h>`, `<stdbool.h>`,
`<string.h>`, and `<math.h>` from the C standard library).

```bash
arm-none-eabi-gcc \
  -mcpu=cortex-m33 \
  -mfpu=fpv5-sp-d16 -mfloat-abi=hard \
  -std=c11 -Wall -Os \
  -c can_id.c spn_decode.c spn_spec.c signal_state.c grid_sample.c
```

All arithmetic uses `float` (32-bit), so every operation maps to a single
FPU instruction on the Cortex-M33.  There is no heap allocation; all state
lives in the `GridSampler` struct that the caller owns.

### Design decisions

| Choice | Rationale |
|---|---|
| `float` (32-bit) throughout | Matches the ONNX model input dtype; uses the hardware FPU on the STM32H533; all SPN scales fit exactly in float32 |
| `uint32_t ms` timestamps | `HAL_GetTick()` is the natural board clock; 1 ms resolution is more than enough for the 1 s gap detector; unsigned subtraction handles the 49-day wraparound |
| `RowCallback` not a ring buffer | Minimises latency and RAM; the callback runs synchronously inside `grid_feed()` |
| `NAN` as "not yet seen" sentinel | One-to-one with Python's `None`; `isnan()` compiles to a single FPU test |
| `signal_index` embedded in `SpnDef` | Avoids any string-keyed lookup at runtime; the column ordering matches the Python `SIGNALS` list at compile time |
| Linear scan over 9 PGNs | Negligible cost (≤ 9 comparisons per frame); no hash table needed |

### Caveats

- `can_log_loader.py` is deliberately not ported.  On the board, frames arrive
  from the CAN peripheral, not from CSV files.  If you need to replay a log
  for testing, send its frames over UART from the PC and read them back with
  a thin receive wrapper.
- The `profile/` sub-module (PGN counts, intervals, classify) is PC-side data
  analysis only and has no place in firmware.
- `grid_feed()` is **not re-entrant**.  If you call it from an ISR and also
  from a task, protect the `GridSampler` with a mutex or critical section.
- The `on_row` callback is called from within `grid_feed()`, so it must not
  block.  If the model inference takes longer than one CAN frame interval
  (~1 ms at 850 frames/s), move it to a lower-priority task and post the row
  to a queue from the callback.
