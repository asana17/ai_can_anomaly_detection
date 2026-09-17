#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DIR/../.." && pwd)"

echo "=========================================================="
echo "  Comparing Python vs. C Preprocess Pipeline"
echo "=========================================================="

echo "[1/4] Compiling C comparison program..."
make -C "$DIR" compare

echo "[2/4] Running C pipeline..."
"$DIR/compare" > "$DIR/c_output.txt"

echo "[3/4] Running Python pipeline..."
PYTHONPATH="$REPO_ROOT" python3 "$DIR/gen_golden.py" > "$DIR/py_output.txt"

echo "[4/4] Comparing outputs..."
python3 "$DIR/verify.py" "$DIR/py_output.txt" "$DIR/c_output.txt"
