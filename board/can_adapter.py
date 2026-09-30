"""The USB-CAN adapter on the PC, and the lines the frames other nodes send are printed as.

The adapter is a candleLight gs_usb one, such as the DSD TECH SH-C31A, run at 250 kbit/s.
On macOS `GsUsbAdapter` opens it over USB and sets the bit rate itself. On Linux
`SocketCanAdapter` sends through the SocketCAN interface the kernel made for it, which
must be up at 250 kbit/s already.
"""

import errno
import re
import socket
import struct
import time

import usb.backend.libusb1
import usb.util
from gs_usb.constants import CAN_EFF_FLAG
from gs_usb.gs_usb import GsUsb
from gs_usb.gs_usb_frame import GS_USB_NONE_ECHO_ID, GsUsbFrame

LIBUSB = "/opt/homebrew/lib/libusb-1.0.dylib"
CAN_FRAME = struct.Struct("=IB3x8s")  # struct can_frame of <linux/can.h>
RECEIVED = re.compile(r"received at ([\d.]+)\s+([0-9A-F]+)\s+\[(\d)\]\s+((?:[0-9A-F]{2} ?)*)")


def frame_text(can_id, data):
    """A frame as gs_usb prints it."""
    return "{: >8X}   [{}]  {}".format(can_id, len(data), " ".join(f"{b:02X}" for b in data))


def received_line(seconds, text):
    """The line of a frame the board sent, `text` as `frame_text` gives it, that came at
    `seconds` since the epoch."""
    return f"received at {seconds:.3f} {text}"


def received_frames(lines):
    """Each line `received_line` gave as (seconds it came, ID, data)."""
    for line in lines:
        found = RECEIVED.match(line.strip())
        if found:
            yield (float(found.group(1)), int(found.group(2), 16),
                   bytes.fromhex(found.group(4)))


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
            print(received_line(time.time(), text), flush=True)
