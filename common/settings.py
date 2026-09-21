"""The parameters of a run. Every script that builds rows from the logs reads them here."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Every value a run is made with, kept together so a run can record all of them."""

    PERIOD: float = 0.1         # seconds between two rows on the grid
    MAX_HOLD: float = 1.0       # seconds, the longest gap between frames a row spans
    MIN_SPEED: float = 5.0      # km/h, the speed a row has to exceed to be scored
    TRAIN: float = 0.75         # share of the seconds above MIN_SPEED before the test cut
    N_SPLITS: int = 4           # blocks the seconds above MIN_SPEED are cut into, by time
    FOLD: int = 3               # the block that is the test set, 0 the first
    CALIBRATION: float = 0.10   # share of the training seconds above MIN_SPEED held out
    BLOCK: float = 20.0         # seconds above MIN_SPEED in one calibration block
    GAP: float = 5.0            # seconds left out around each block and the test span
    DONORS: int = 24            # non-test logs the replayed payloads are taken from
    SEED: int = 0               # the rng the attacks are drawn with
    COMPONENTS: tuple = (2, 4, 6, 8, 10, 12, 14, 16)
    TARGET: float = 0.001       # share of normal rows the threshold cuts off
    MOVED: float = 1.0          # z distance a replay must push a row by to be an anomaly
    HOLD: tuple = (1, 10)       # rows a flag must persist before it counts as an alarm
    EPOCHS: int = 1000          # the most passes an autoencoder may make over the rows
    BATCH: int = 1024           # training rows in each update of an autoencoder's weights
    RATE: float = 1e-3          # Adam's learning rate
    IMPROVEMENT: float = 1e-4   # share of the best loss an epoch must cut, fit's threshold
    PATIENCE: int = 10          # epochs in a row without that before training stops
    TORCH_SEED: int = 3         # the torch rng each autoencoder is built and trained with
    HIDDEN: tuple = (32, 64, 128)  # hidden units of a nonlinear autoencoder, each reported

