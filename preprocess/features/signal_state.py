"""Hold-last state: keep the latest value of each tracked signal."""

from __future__ import annotations

from preprocess.frames.spn_spec import SPEC

SIGNALS = [d.name for defs in SPEC.values() for d in defs]


class SignalState:
    def __init__(self, signals=SIGNALS):
        self._signals = list(signals)
        self._values = {name: None for name in self._signals}

    def update(self, values: dict) -> None:
        for name, value in values.items():
            if name in self._values:
                self._values[name] = value

    def snapshot(self) -> list:
        return [self._values[name] for name in self._signals]

    def ready(self) -> bool:
        return all(value is not None for value in self._values.values())
