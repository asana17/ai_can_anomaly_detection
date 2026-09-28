"""Frames the replay tests build their logs from."""

from preprocess.frames.can_log_loader import CanFrame

CCVS1, EEC1 = 0x18FEF1E6, 0x18F004E6


def speed_frame(t, kmh):
    raw = round(kmh / 0.00390625)
    return CanFrame(t, CCVS1, bytes([0, raw & 0xFF, (raw >> 8) & 0xFF, 0, 0, 0, 0, 0]))


def rpm_frame(t, rpm):
    raw = round(rpm / 0.125)
    return CanFrame(t, EEC1, bytes([0, 0, 0, raw & 0xFF, (raw >> 8) & 0xFF, 0, 0, 0]))
