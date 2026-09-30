"""Send one log's frames from the USB-CAN adapter, each at its time.

    python3 -m board.application.ai_can_anomaly_detection.send_test_frames LOG

LOG is a log of `fetched/frames/frames.parquet`, as for `expected.py`. The adapter is a
candleLight gs_usb one, such as the DSD TECH SH-C31A, run at 250 kbit/s. On macOS the
script opens it over USB and sets the bit rate itself. On Linux it sends through the
SocketCAN interface the kernel made for it, `can0` unless `--interface` names another,
which must be up at 250 kbit/s already. It prints the time sending started, as epoch
seconds, and how late the frames were handed to the adapter, both to stderr. Each frame
another node sends, such as the board's alarm frame, is printed to stdout with the epoch
seconds it came.
"""

import argparse
import errno
import socket
import struct
import sys
import threading
import time

import numpy as np
import usb.backend.libusb1
import usb.util
from gs_usb.constants import CAN_EFF_FLAG
from gs_usb.gs_usb import GsUsb
from gs_usb.gs_usb_frame import GS_USB_NONE_ECHO_ID, GsUsbFrame

from board.application.ai_can_anomaly_detection.expected import frames

LIBUSB = "/opt/homebrew/lib/libusb-1.0.dylib"
SPIN = 0.002  # s before a frame's time to stop sleeping and spin
CAN_FRAME = struct.Struct("=IB3x8s")  # struct can_frame of <linux/can.h>


def frame_text(can_id, data):
    """A frame as gs_usb prints it, which board_frames reads."""
    return "{: >8X}   [{}]  {}".format(can_id, len(data), " ".join(f"{b:02X}" for b in data))


class GsUsbAdapter:
    """The first gs_usb adapter, opened over USB on macOS and started at 250 kbit/s."""

    def __init__(self):
        # pyusb finds no libusb by itself on the Mac, and gs_usb reuses what is loaded here
        usb.backend.libusb1.get_backend(find_library=lambda _: LIBUSB)
        adapters = GsUsb.scan()
        if not adapters:
            raise SystemExit("no gs_usb adapter found")
        self.dev = adapters[0]
        # macOS has no kernel driver to detach, and asking is denied
        self.dev.gs_usb.is_kernel_driver_active = lambda interface: False
        # 250 kbit/s on the adapter's 170 MHz clock, sample point at 87 %
        self.dev.set_timing(prop_seg=1, phase_seg1=57, phase_seg2=9, sjw=9, brp=10)
        self.dev.start()

    def send(self, can_id, data):
        self.dev.send(GsUsbFrame(can_id=can_id | CAN_EFF_FLAG, data=data))

    def read(self):
        """(True, None) for a frame of ours the adapter has queued, (False, text) for
        another node's frame, None when nothing came within 100 ms."""
        frame = GsUsbFrame()
        if not self.dev.read(frame, 100):
            return None
        if frame.echo_id == GS_USB_NONE_ECHO_ID:
            return False, str(frame)
        return True, None

    def close(self):
        self.dev.stop()
        # without this the next open reads nothing until the adapter is plugged in again
        usb.util.dispose_resources(self.dev.gs_usb)


class SocketCanAdapter:
    """A SocketCAN interface on Linux, already up at 250 kbit/s."""

    def __init__(self, interface):
        self.sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        # our own frames come back, flagged MSG_CONFIRM, once the adapter has sent them
        self.sock.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_RECV_OWN_MSGS, 1)
        self.sock.settimeout(0.1)
        try:
            self.sock.bind((interface,))
        except OSError as e:
            raise SystemExit(f"cannot open {interface}: {e}")

    def send(self, can_id, data):
        packed = CAN_FRAME.pack(can_id | socket.CAN_EFF_FLAG, len(data), bytes(data))
        while True:
            try:
                self.sock.send(packed)
                return
            except OSError as e:
                # the interface's queue is full; wait for the adapter to take a frame
                if e.errno != errno.ENOBUFS:
                    raise
                time.sleep(0.0005)

    def read(self):
        """(True, None) for a frame of ours the adapter has sent, (False, text) for
        another node's frame, None when nothing came within 100 ms."""
        try:
            packed, _, flags, _ = self.sock.recvmsg(CAN_FRAME.size)
        except socket.timeout:
            return None
        if flags & socket.MSG_CONFIRM:
            return True, None
        can_id, length, data = CAN_FRAME.unpack(packed)
        return False, frame_text(can_id & socket.CAN_EFF_MASK, data[:length])

    def close(self):
        self.sock.close()


def read_frames(adapter, stop, echoes):
    """Count the frames the adapter hands back once it has queued them, and print the
    frames other nodes send."""
    while not stop.is_set():
        got = adapter.read()
        if got is None:
            continue
        ours, text = got
        if ours:
            echoes[0] += 1
        else:
            print(f"received at {time.time():.3f} {text}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log")
    parser.add_argument("--interface", default="can0",
                        help="the SocketCAN interface on Linux (default can0)")
    args = parser.parse_args()

    sent = frames(args.log)
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
