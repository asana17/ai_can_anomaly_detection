#!/usr/bin/env python3
"""
gen_golden.py — Run synthetic CAN frames through the Python preprocess
pipeline and print one row per line (space-separated floats).

Output is compared against the C implementation by run_compare.sh.

Run from the repo root:
    python3 preprocess_c/compare/gen_golden.py
"""
import sys
import os

# Allow importing from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from preprocess.frames.can_log_loader import CanFrame
from preprocess.features.grid_sample import resample

# ---------------------------------------------------------------------------
# Synthetic CAN frames
#
# These frames cover all 9 decoded PGNs and produce known physical values.
# The same bytes are hardcoded in compare.c so both pipelines see identical
# input.
#
# Arbitration ID construction:  arb_id = (priority<<26) | (pgn<<8) | sa
# All frames: priority=6, sa=0xE6 (except CCVS1 which uses sa=0x21).
#
# Payload values (expected row):
#   engine_speed          2000.000 rpm
#   driver_demand_torque    50.000 %
#   actual_engine_torque    60.000 %
#   accel_pedal             30.000 %
#   engine_load             40.000 %
#   wheel_speed             80.000 km/h
#   fuel_rate               25.000 L/h
#   output_shaft_speed    1200.000 rpm
#   clutch_slip              0.000 %
#   input_shaft_speed     1200.000 rpm
#   selected_gear            6.000 gear
#   current_gear             6.000 gear
#   tachograph_speed        80.000 km/h
#   brake_pedal              0.000 %
#   steering_angle         -31.374 rad   (raw=0, offset=-31.374)
#   yaw_rate                -3.920 rad/s (raw=0, offset=-3.92)
#   lateral_accel          -15.687 m/s²  (raw=0, offset=-15.687)
# ---------------------------------------------------------------------------

FRAMES = [
    # ---- t = 0.000 s: seed every signal ----

    # EEC1 (PGN 61444 = 0xF004) arb_id=0x18F004E6
    #   bytes[1]=0xAF  driver_demand_torque raw=175 → 175-125=50%
    #   bytes[2]=0xB9  actual_engine_torque raw=185 → 185-125=60%
    #   bytes[3-4]=0x803E LE  engine_speed raw=16000 → 16000*0.125=2000 rpm
    CanFrame(0.000, 0x18F004E6,
             bytes([0x00, 0xAF, 0xB9, 0x80, 0x3E, 0x00, 0x00, 0x00])),

    # EEC2 (PGN 61443 = 0xF003) arb_id=0x18F003E6
    #   bytes[1]=0x4B  accel_pedal raw=75 → 75*0.4=30%
    #   bytes[2]=0x28  engine_load raw=40 → 40*1.0=40%
    CanFrame(0.000, 0x18F003E6,
             bytes([0x00, 0x4B, 0x28, 0x00, 0x00, 0x00, 0x00, 0x00])),

    # CCVS1 (PGN 65265 = 0xFEF1) arb_id=0x18FEF121
    #   bytes[1-2]=0x0050 LE  wheel_speed raw=20480 → 20480/256=80 km/h
    CanFrame(0.000, 0x18FEF121,
             bytes([0x00, 0x00, 0x50, 0x00, 0x00, 0x00, 0x00, 0x00])),

    # LFE1 (PGN 65266 = 0xFEF2) arb_id=0x18FEF2E6
    #   bytes[0-1]=0xF401 LE  fuel_rate raw=500 → 500*0.05=25 L/h
    CanFrame(0.000, 0x18FEF2E6,
             bytes([0xF4, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),

    # ETC1 (PGN 61442 = 0xF002) arb_id=0x18F002E6
    #   bytes[1-2]=0x8025 LE  output_shaft_speed raw=9600 → 9600*0.125=1200 rpm
    #   bytes[3]=0x00          clutch_slip raw=0 → 0%
    #   bytes[5-6]=0x8025 LE  input_shaft_speed raw=9600 → 1200 rpm
    CanFrame(0.000, 0x18F002E6,
             bytes([0x00, 0x80, 0x25, 0x00, 0x00, 0x80, 0x25, 0x00])),

    # ETC2 (PGN 61445 = 0xF005) arb_id=0x18F005E6
    #   bytes[0]=0x83  selected_gear raw=131 → 131-125=6
    #   bytes[3]=0x83  current_gear  raw=131 → 131-125=6
    CanFrame(0.000, 0x18F005E6,
             bytes([0x83, 0x00, 0x00, 0x83, 0x00, 0x00, 0x00, 0x00])),

    # TCO1 (PGN 65132 = 0xFE6C) arb_id=0x18FE6CE6
    #   bytes[6-7]=0x0050 LE  tachograph_speed raw=20480 → 80 km/h
    CanFrame(0.000, 0x18FE6CE6,
             bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x50])),

    # EBC1 (PGN 61441 = 0xF001) arb_id=0x18F001E6
    #   bytes[1]=0x00  brake_pedal raw=0 → 0%
    CanFrame(0.000, 0x18F001E6,
             bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),

    # VDC2 (PGN 61449 = 0xF009) arb_id=0x18F009E6
    #   All zeros → raw=0 for all three SPNs.
    #   steering_angle = 0*(1/1024) + (-31.374) = -31.374 rad
    #   yaw_rate       = 0*(1/8192) + (-3.92)   = -3.920 rad/s
    #   lateral_accel  = 0*(1/2048) + (-15.687) = -15.687 m/s²
    CanFrame(0.000, 0x18F009E6,
             bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),

    # ---- t = 0.100 s: triggers grid tick at t=0.100 ----
    CanFrame(0.100, 0x18F004E6,
             bytes([0x00, 0xAF, 0xB9, 0x80, 0x3E, 0x00, 0x00, 0x00])),

    # ---- t = 0.200 s: triggers grid tick at t=0.200 ----
    CanFrame(0.200, 0x18F004E6,
             bytes([0x00, 0xAF, 0xB9, 0x80, 0x3E, 0x00, 0x00, 0x00])),
]

if __name__ == '__main__':
    for _t, row in resample(FRAMES, period=0.1, max_hold=1.0):
        print(' '.join(f'{v:.6f}' for v in row))
