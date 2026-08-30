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
}
