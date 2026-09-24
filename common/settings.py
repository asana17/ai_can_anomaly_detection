"""The parameters of a run, one class for each stage that reads any.

A stage takes its own class alone. A value one stage fixes and a later one needs, such
as the speed the log split was cut at, comes from the earlier stage's `meta.json`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields


@dataclass(frozen=True)
class GridSettings:
    PERIOD: float = 0.1         # seconds between two rows on the grid
    MAX_HOLD: float = 1.0       # seconds, the longest gap between frames a row spans


@dataclass(frozen=True)
class SplitSettings:
    MIN_SPEED: float = 5.0      # km/h, the speed a row has to exceed to be scored
    N_SPLITS: int = 4           # blocks the seconds above MIN_SPEED are cut into, by time
    FOLD: int = 3               # the block that is the test set, 0 the first


@dataclass(frozen=True)
class CalibrationSettings:
    CALIBRATION: float = 0.10   # share of the training seconds above MIN_SPEED held out
    BLOCK: float = 20.0         # seconds above MIN_SPEED in one calibration block
    GAP: float = 5.0            # seconds left out between the blocks and the test span


@dataclass(frozen=True)
class TrainSettings:
    GAP: float = 5.0            # seconds left out around each block and the test span


@dataclass(frozen=True)
class TestSetSettings:
    ATTACK: str = "replay"      # the kind of attack, replay or matched_replay
    DONORS: int = 24            # non-test logs the replayed payloads are taken from
    SEED: int = 0               # the rng the attacks are drawn with


@dataclass(frozen=True)
class CalibrateSettings:
    TARGET: float = 0.001       # share of normal rows the threshold cuts off


@dataclass(frozen=True)
class TestRunSettings:
    MOVED: float = 1.0          # z distance a replay must push a row by to be an anomaly
    HOLD: tuple = (1, 10)       # rows a flag must persist before it counts as an alarm


@dataclass(frozen=True)
class QuantizeSettings:
    BATCH: int = 1024           # training rows in each update of an autoencoder's weights


@dataclass(frozen=True)
class PipelineSettings:
    """Where a run reads and writes. A relative folder is taken from where the pipeline
    is started."""

    data_repo: str = "asana17/ai_can_anomaly_detection_data"
    runs_repo: str = "asana17/ai_can_anomaly_detection_runs"
    can_data_dir: str = "data"
    can_data_pattern: str = "part_*/*.csv"
    local_data_dir: str = "out/data"
    local_runs_dir: str = "out/runs"
    snapshot_dir: str = "out/snapshots"


@dataclass(frozen=True)
class RunSettings:
    """Every stage's settings, each under the name of the stage that reads them, and
    the pipeline's."""

    pipeline: PipelineSettings = PipelineSettings()
    grid: GridSettings = GridSettings()
    split_test_logs: SplitSettings = SplitSettings()
    calibration_set: CalibrationSettings = CalibrationSettings()
    train_set: TrainSettings = TrainSettings()
    test_set: TestSetSettings = TestSetSettings()
    calibrate: CalibrateSettings = CalibrateSettings()
    run_test_set: TestRunSettings = TestRunSettings()
    quantize: QuantizeSettings = QuantizeSettings()


def read_settings(path):
    """`RunSettings` with the values the JSON file `path` names in place of the
    defaults.

    The file holds an object for each stage it changes, such as
    `{"split_test_logs": {"FOLD": 0}}`. A stage or a name the classes do not have
    raises.
    """
    with open(path) as f:
        values = json.load(f)
    kinds = {field.name: type(field.default) for field in fields(RunSettings)}
    unknown = set(values) - set(kinds)
    if unknown:
        raise ValueError(f"no stage takes settings named {sorted(unknown)}")
    return RunSettings(**{
        stage: kinds[stage](**{name: tuple(value) if isinstance(value, list) else value
                               for name, value in changed.items()})
        for stage, changed in values.items()})
