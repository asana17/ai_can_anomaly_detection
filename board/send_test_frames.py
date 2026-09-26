"""Send the nine J1939 frames ai_can_anomaly_detection's model reads.

The board decodes nine PGNs (preprocess/frames/spn_spec.py, mirrored in
board/lib/spn_decode/spn_spec.h). Its inference runs a row only once every PGN
has arrived (signal_state_ready) and the wheel speed exceeds 5 km/h (moving).
This builds one frame per PGN from fixed "moving / normal" physical values and
sends them over SocketCAN as extended 29-bit IDs, so that path fires.

Self-contained: the SPEC and values are inlined and it sends through a raw
AF_CAN socket, so it needs neither numpy nor python-can. Run it on the Linux
box wired to the board.

Bring the bus up first (matching the board's 250 kbps):
    sudo ip link set can0 type can bitrate 250000
    sudo ip link set can0 up

Then, from the repo root:
    python3 board/send_test_frames.py            # send every second on can0
    python3 board/send_test_frames.py --once     # send one round and exit
    python3 board/send_test_frames.py --print    # just print cansend lines
    python3 board/send_test_frames.py -i can1 -p 0.5
"""

from __future__ import annotations

import argparse
import socket
import struct
import time

# (name, start_bit, length, scale, offset) per PGN, copied from spn_spec.py.
# Keep in step with preprocess/frames/spn_spec.py and board/lib/spn_decode/spn_spec.h.
SPEC: dict[int, list[tuple[str, int, int, float, float]]] = {
    61444: [("engine_speed", 24, 16, 0.125, 0.0),
            ("driver_demand_torque", 8, 8, 1.0, -125.0),
            ("actual_engine_torque", 16, 8, 1.0, -125.0)],
    61443: [("accel_pedal", 8, 8, 0.4, 0.0),
            ("engine_load", 16, 8, 1.0, 0.0)],
    65265: [("wheel_speed", 8, 16, 0.00390625, 0.0)],
    65266: [("fuel_rate", 0, 16, 0.05, 0.0)],
    61442: [("output_shaft_speed", 8, 16, 0.125, 0.0),
            ("clutch_slip", 24, 8, 0.4, 0.0),
            ("input_shaft_speed", 40, 16, 0.125, 0.0)],
    61445: [("selected_gear", 0, 8, 1.0, -125.0),
            ("current_gear", 24, 8, 1.0, -125.0)],
    65132: [("tachograph_speed", 48, 16, 1 / 256, 0.0)],
    61441: [("brake_pedal", 8, 8, 0.4, 0.0)],
    61449: [("steering_angle", 0, 16, 1 / 1024, -31.374),
            ("yaw_rate", 24, 16, 1 / 8192, -3.92),
            ("lateral_accel", 40, 16, 1 / 2048, -15.687)],
}

# Fixed physical values, all in their normal range; wheel_speed > 5 so moving() passes.
VALUES: dict[str, float] = {
    "engine_speed": 1000.0, "driver_demand_torque": 40.0, "actual_engine_torque": 45.0,
    "accel_pedal": 40.0, "engine_load": 50.0,
    "wheel_speed": 50.0,
    "fuel_rate": 20.0,
    "output_shaft_speed": 762.5, "clutch_slip": 0.0, "input_shaft_speed": 762.5,
    "selected_gear": 5.0, "current_gear": 5.0,
    "tachograph_speed": 50.0,
    "brake_pedal": 0.0,
    "steering_angle": 0.0, "yaw_rate": 0.0, "lateral_accel": 0.0,
}

PRIORITY = 6           # J1939 default for these PGNs
SOURCE_ADDRESS = 0x00

# struct can_frame from <linux/can.h>: __u32 can_id; __u8 len, pad, res0, res1; __u8 data[8]
_CAN_FRAME_FMT = "=IB3x8s"
_CAN_EFF_FLAG = 0x80000000


def arb_id(pgn: int) -> int:
    """The 29-bit arbitration ID for a PGN at the fixed priority and source address.

    pgn << 8 places data page, PDU format and (for PDU2) PDU specific where the ID
    wants them; PDU1's destination address is left 0, so one formula serves both.
    decompose_can_id in preprocess/frames recovers this exact PGN.
    """
    return (PRIORITY << 26) | (pgn << 8) | SOURCE_ADDRESS


def payload(pgn: int) -> bytes:
    """The eight-byte payload for a PGN, unused bytes left 0xFF (not available)."""
    data = bytearray(b"\xff" * 8)
    for name, start_bit, length, scale, offset in SPEC[pgn]:
        raw = round((VALUES[name] - offset) / scale)
        if not 0 <= raw < (1 << length):
            raise ValueError(f"{name}={VALUES[name]} out of range for {length} bits")
        if raw >> max(length - 8, 0) >= 0xFE:       # 0xFE/0xFF decode as reserved
            raise ValueError(f"{name}={VALUES[name]} decodes as reserved")
        data[start_bit // 8:start_bit // 8 + length // 8] = raw.to_bytes(length // 8, "little")
    return bytes(data)


def frames() -> list[tuple[int, bytes]]:
    """Every (arb_id, payload) the model reads, one per PGN."""
    return [(arb_id(pgn), payload(pgn)) for pgn in SPEC]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--interface", default="can0", help="SocketCAN interface")
    parser.add_argument("-p", "--period", type=float, default=1.0,
                        help="seconds between rounds")
    parser.add_argument("--once", action="store_true", help="send one round and exit")
    parser.add_argument("--print", dest="show", action="store_true",
                        help="print cansend lines instead of sending")
    args = parser.parse_args()

    if args.show:
        for aid, data in frames():
            print(f"cansend {args.interface} {aid:08X}#{data.hex().upper()}")
        return

    sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    sock.bind((args.interface,))
    try:
        while True:
            for aid, data in frames():
                packet = struct.pack(_CAN_FRAME_FMT, aid | _CAN_EFF_FLAG, len(data), data)
                sock.send(packet)
            if args.once:
                break
            time.sleep(args.period)
    finally:
        sock.close()


if __name__ == "__main__":
    main()
