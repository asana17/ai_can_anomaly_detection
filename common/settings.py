"""The parameters of a run. Every script that builds rows from the logs reads them here."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Every value a run is made with, kept together so a run can record all of them."""

    PERIOD: float = 0.1         # seconds between two rows on the grid
    MAX_HOLD: float = 1.0       # seconds, the longest gap between frames a row spans
    MIN_SPEED: float = 5.0      # km/h, the speed a row has to exceed to be scored
    N_SPLITS: int = 4           # blocks the seconds above MIN_SPEED are cut into, by time
    FOLD: int = 3               # the block that is the test set, 0 the first
    CALIBRATION: float = 0.10   # share of the training seconds above MIN_SPEED held out
    BLOCK: float = 20.0         # seconds above MIN_SPEED in one calibration block
    GAP: float = 5.0            # seconds left out around each block and the test span
    DONORS: int = 24            # non-test logs the replayed payloads are taken from
    SEED: int = 0               # the rng the attacks are drawn with
    TARGET: float = 0.001       # share of normal rows the threshold cuts off
    MOVED: float = 1.0          # z distance a replay must push a row by to be an anomaly
    HOLD: tuple = (1, 10)       # rows a flag must persist before it counts as an alarm
    BATCH: int = 1024           # training rows in each update of an autoencoder's weights


def read_settings(path):
    """`Settings` with the values the JSON file `path` names in place of the defaults.

    `path` None gives the defaults. A name `Settings` does not have raises.
    """
    if path is None:
        return Settings()
    with open(path) as f:
        values = json.load(f)
    return Settings(**{name: tuple(value) if isinstance(value, list) else value
                       for name, value in values.items()})
