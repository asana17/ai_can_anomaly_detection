"""Flag any signal that falls outside the range J1939 defines for it."""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS
from preprocess.frames.spn_spec import SPEC

LIMITS = {d.name: (d.minimum, d.maximum) for defs in SPEC.values() for d in defs}


def hits(raw: np.ndarray) -> np.ndarray:
    """True where any signal of a row sits outside its range, or is NaN."""
    low = np.array([LIMITS[name][0] for name in SIGNALS])
    high = np.array([LIMITS[name][1] for name in SIGNALS])
    return ~((raw >= low) & (raw <= high)).all(axis=1)
