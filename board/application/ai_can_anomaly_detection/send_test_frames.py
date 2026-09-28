"""Send one log's frames from the USB-CAN adapter on macOS, each at its time.

    python3 -m board.application.ai_can_anomaly_detection.send_test_frames LOG

LOG is a log of `fetched/frames/frames.parquet`, as for `expected.py`. The adapter is a
candleLight gs_usb one, such as the DSD TECH SH-C31A, run at 250 kbit/s. It prints the
time sending started, as epoch seconds, and how late the frames were handed to the
adapter.
"""

import argparse
import threading
import time

import numpy as np
import usb.backend.libusb1
import usb.util
from gs_usb.constants import CAN_EFF_FLAG
from gs_usb.gs_usb import GsUsb
from gs_usb.gs_usb_frame import GsUsbFrame

from board.application.ai_can_anomaly_detection.expected import frames

LIBUSB = "/opt/homebrew/lib/libusb-1.0.dylib"
SPIN = 0.002  # s before a frame's time to stop sleeping and spin


def open_adapter():
    """The first gs_usb adapter, started at 250 kbit/s."""
    # pyusb finds no libusb by itself on the Mac, and gs_usb reuses what is loaded here
    usb.backend.libusb1.get_backend(find_library=lambda _: LIBUSB)
    adapters = GsUsb.scan()
    if not adapters:
        raise SystemExit("no gs_usb adapter found")
    dev = adapters[0]
    # macOS has no kernel driver to detach, and asking is denied
    dev.gs_usb.is_kernel_driver_active = lambda interface: False
    # 250 kbit/s on the adapter's 170 MHz clock, sample point at 87 %
    dev.set_timing(prop_seg=1, phase_seg1=57, phase_seg2=9, sjw=9, brp=10)
    dev.start()
    return dev


def close_adapter(dev):
    dev.stop()
    # without this the next open reads nothing until the adapter is plugged in again
    usb.util.dispose_resources(dev.gs_usb)


def read_echoes(dev, stop, echoes):
    """Count the frames the adapter hands back once it has queued them."""
    frame = GsUsbFrame()
    while not stop.is_set():
        if dev.read(frame, 100):
            echoes[0] += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log")
    args = parser.parse_args()

    sent = frames(args.log)
    first = sent[0].timestamp
    late = np.empty(len(sent))
    echoes = [0]
    stop = threading.Event()
    dev = open_adapter()
    reader = threading.Thread(target=read_echoes, args=(dev, stop, echoes))
    reader.start()
    try:
        start = time.perf_counter()
        print(f"sending {len(sent)} frames from {time.time():.3f}", flush=True)
        for i, frame in enumerate(sent):
            target = frame.timestamp - first
            while True:
                left = target - (time.perf_counter() - start)
                if left <= 0:
                    break
                if left > SPIN:
                    time.sleep(left - SPIN)
            late[i] = time.perf_counter() - start - target
            dev.send(GsUsbFrame(can_id=frame.can_id | CAN_EFF_FLAG, data=frame.data))
        time.sleep(0.5)  # let the last echoes come back
    finally:
        stop.set()
        reader.join()
        close_adapter(dev)
    ms = late * 1e3
    print(f"sent {len(sent)}, echoed {echoes[0]}, late ms median {np.median(ms):.3f}, "
          f"p99 {np.percentile(ms, 99):.3f}, max {ms.max():.3f}")


if __name__ == "__main__":
    main()
