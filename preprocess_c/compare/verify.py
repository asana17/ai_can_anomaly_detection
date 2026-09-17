#!/usr/bin/env python3
"""
verify.py — Numerically compare Python vs. C preprocess pipeline outputs.

Compares rows column-by-column, checking that all 17 signals agree within
single-precision floating-point tolerance (|py - c| < 1e-4).
"""
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from preprocess.features.signal_state import SIGNALS

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 verify.py <python_output.txt> <c_output.txt>")
        sys.exit(1)

    py_file, c_file = sys.argv[1], sys.argv[2]

    with open(py_file, 'r') as f:
        py_lines = [line.strip() for line in f if line.strip()]
    with open(c_file, 'r') as f:
        c_lines = [line.strip() for line in f if line.strip()]

    print("=" * 80)
    print("        PREPROCESS PIPELINE OUTPUT COMPARISON: Python vs. C")
    print("=" * 80)
    print(f"Python output file: {py_file} ({len(py_lines)} rows)")
    print(f"C output file:      {c_file} ({len(c_lines)} rows)")

    if len(py_lines) != len(c_lines):
        print(f"\n[ERROR] Row count mismatch! Python produced {len(py_lines)} rows, C produced {len(c_lines)} rows.")
        sys.exit(1)

    if len(py_lines) == 0:
        print("\n[WARNING] Both outputs are empty. Nothing to compare.")
        sys.exit(1)

    py_rows = [[float(x) for x in line.split()] for line in py_lines]
    c_rows = [[float(x) for x in line.split()] for line in c_lines]

    TOLERANCE = 1e-4
    max_diffs = [0.0] * len(SIGNALS)
    total_elements = 0
    exact_matches = 0
    within_tolerance = 0
    failed = False

    for row_idx, (py_r, c_r) in enumerate(zip(py_rows, c_rows)):
        if len(py_r) != len(SIGNALS) or len(c_r) != len(SIGNALS):
            print(f"[ERROR] Row {row_idx + 1} column count mismatch: "
                  f"Python has {len(py_r)}, C has {len(c_r)}, expected {len(SIGNALS)}")
            sys.exit(1)

        for col_idx, (p_val, c_val) in enumerate(zip(py_r, c_r)):
            diff = abs(p_val - c_val)
            if diff > max_diffs[col_idx]:
                max_diffs[col_idx] = diff

            total_elements += 1
            if diff == 0.0:
                exact_matches += 1
            if diff <= TOLERANCE:
                within_tolerance += 1
            else:
                failed = True
                print(f"[MISMATCH] Row {row_idx + 1}, Col {col_idx} ({SIGNALS[col_idx]}): "
                      f"Py={p_val:.6f}, C={c_val:.6f}, diff={diff:.6e}")

    print("\n--- Per-Signal Comparison Summary across all rows ---")
    print(f"{'Idx':<4} | {'Signal Name':<22} | {'Max Abs Diff':<14} | {'Status (< 1e-4)':<15}")
    print("-" * 62)
    for idx, (name, max_d) in enumerate(zip(SIGNALS, max_diffs)):
        status = "EXACT (0.0)" if max_d == 0.0 else f"PASS ({max_d:.1e})" if max_d <= TOLERANCE else "FAIL"
        print(f"{idx:<4} | {name:<22} | {max_d:<14.2e} | {status:<15}")

    print("\n--- Summary Statistics ---")
    print(f"Total Values Compared:  {total_elements} ({len(py_rows)} rows x {len(SIGNALS)} signals)")
    print(f"Exact Matches (0.0):    {exact_matches}/{total_elements} ({exact_matches/total_elements*100:.1f}%)")
    print(f"Within Tolerance (1e-4): {within_tolerance}/{total_elements} ({within_tolerance/total_elements*100:.1f}%)")
    max_overall_diff = max(max_diffs)
    print(f"Max Difference Observed: {max_overall_diff:.2e}")

    if not failed:
        print("\n[RESULT] SUCCESS: Python and C implementations produce EQUIVALENT outputs!")
        sys.exit(0)
    else:
        print("\n[RESULT] FAILURE: Discrepancies exceed tolerance!")
        sys.exit(1)

if __name__ == '__main__':
    main()
