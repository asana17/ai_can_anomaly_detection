"""Send one log's frames from the USB-CAN adapter, each at its time.

    python3 -m board.application.ai_can_anomaly_detection.send_test_frames LOG [--frames FRAMES]

LOG and FRAMES are as for `expected.py`. The adapter is a
candleLight gs_usb one, such as the DSD TECH SH-C31A, run at 250 kbit/s. On macOS the
script opens it over USB and sets the bit rate itself. On Linux it sends through the
SocketCAN interface the kernel made for it, `can0` unless `--interface` names another,
which must be up at 250 kbit/s already. It prints the time sending started, as epoch
seconds, and how late the frames were handed to the adapter, both to stderr. Each frame
another node sends, such as the board's alarm frame, is printed to stdout with the epoch
seconds it came.
"""

import argparse
import sys
import threading
import time
from pathlib import Path

import numpy as np

from board.application.ai_can_anomaly_detection.frames_common import FRAMES, frames_of_log
from board.can_adapter import GsUsbAdapter, SocketCanAdapter, read_frames

SPIN = 0.002  # s before a frame's time to stop sleeping and spin


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log")
    parser.add_argument("--frames", type=Path, default=FRAMES)
    parser.add_argument("--interface", default="can0",
                        help="the SocketCAN interface on Linux (default can0)")
    args = parser.parse_args()

    sent = frames_of_log(args.log, args.frames)
    first = sent[0].timestamp
    late = np.empty(len(sent))
    echoes = [0]
    stop = threading.Event()
    adapter = GsUsbAdapter() if sys.platform == "darwin" else SocketCanAdapter(args.interface)
    reader = threading.Thread(target=read_frames, args=(adapter, stop, echoes))
    reader.start()
    try:
        start = time.perf_counter()
        print(f"sending {len(sent)} frames from {time.time():.3f}", file=sys.stderr)
        for i, frame in enumerate(sent):
            target = frame.timestamp - first
            while True:
                left = target - (time.perf_counter() - start)
                if left <= 0:
                    break
                if left > SPIN:
                    time.sleep(left - SPIN)
            late[i] = time.perf_counter() - start - target
            adapter.send(frame.can_id, frame.data)
        time.sleep(0.5)  # let the last echoes come back
    finally:
        stop.set()
        reader.join()
        adapter.close()
    ms = late * 1e3
    print(f"sent {len(sent)}, echoed {echoes[0]}, late ms median {np.median(ms):.3f}, "
          f"p99 {np.percentile(ms, 99):.3f}, max {ms.max():.3f}", file=sys.stderr)


if __name__ == "__main__":
    main()
