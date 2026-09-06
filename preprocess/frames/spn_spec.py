"""SPN decode table: which SPNs each PGN carries and how to decode them."""

from __future__ import annotations

from typing import NamedTuple

from preprocess.frames.spn_decode import SpnField


class SpnDef(NamedTuple):
    spn: int
    name: str
    unit: str
    field: SpnField     # start_bit, length, scale, offset
    minimum: float      # J1939 defined range
    maximum: float


SPEC: dict[int, list[SpnDef]] = {
    61444: [  # EEC1
        SpnDef(190, "engine_speed", "rpm", SpnField(24, 16, 0.125, 0.0), 0.0, 8031.875),
        SpnDef(512, "driver_demand_torque", "%", SpnField(8, 8, 1.0, -125.0), -125.0, 125.0),
        SpnDef(513, "actual_engine_torque", "%", SpnField(16, 8, 1.0, -125.0), -125.0, 125.0),
    ],
    61443: [  # EEC2
        SpnDef(91, "accel_pedal", "%", SpnField(8, 8, 0.4, 0.0), 0.0, 100.0),
        SpnDef(92, "engine_load", "%", SpnField(16, 8, 1.0, 0.0), 0.0, 250.0),
    ],
    65265: [  # CCVS1
        SpnDef(84, "wheel_speed", "km/h", SpnField(8, 16, 0.00390625, 0.0), 0.0, 250.996),
    ],
    65266: [  # LFE1
        SpnDef(183, "fuel_rate", "L/h", SpnField(0, 16, 0.05, 0.0), 0.0, 3212.75),
        # SPN 184 (instant fuel economy) is always NA in this data, so it is omitted.
    ],
    65132: [  # TCO1, bytes 7-8 confirmed against CCVS1, the two agree to 0.9 km/h
             # at p99. A second reading of the same quantity, so an attack that
             # moves one message and not the other shows up as the two disagreeing
        SpnDef(1624, "tachograph_speed", "km/h", SpnField(48, 16, 1 / 256, 0.0),
               0.0, 250.996),
    ],
    61441: [  # EBC1, byte 2 confirmed by deceleration deepening with the pedal,
             # from -0.19 m/s2 just off the stop to -1.25 m/s2 past 30%
        SpnDef(521, "brake_pedal", "%", SpnField(8, 8, 0.4, 0.0), 0.0, 100.0),
        # bytes 1 and 3 are status bits and 4 to 8 are always NA, so all are omitted
    ],
    61449: [  # VDC2, positions confirmed on 196,145 moving samples
        # steering and yaw correlate at 0.99, which only two readings of one turn would
        SpnDef(1807, "steering_angle", "rad", SpnField(0, 16, 1 / 1024, -31.374),
               -31.374, 31.374),
        SpnDef(1811, "yaw_rate", "rad/s", SpnField(24, 16, 1 / 8192, -3.92),
               -3.92, 3.92),
        # tracks speed times yaw at 0.97 in hard cornering. The slope is 0.75, from
        # body roll and road camber, not from a scale error, which would hold it flat
        SpnDef(1809, "lateral_accel", "m/s2", SpnField(40, 16, 1 / 2048, -15.687),
               -15.687, 15.687),
        # SPN 1810 (longitudinal acceleration) is byte 8 and always NA, so it is
        # omitted, the same as SPN 184 above.
    ],
}
