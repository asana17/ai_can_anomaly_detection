"""Flag any signal that falls outside the range J1939 defines for it."""

from __future__ import annotations

import numpy as np

from preprocess.features.signal_state import SIGNALS
from preprocess.frames.spn_spec import SPEC

LIMITS = {d.name: (d.minimum, d.maximum) for defs in SPEC.values() for d in defs}


def hits(raw: np.ndarray) -> np.ndarray:
    """True where any signal of a row sits outside its range, or is NaN."""
    # A grid row holds float32, so the limits are float32 too.
    # In float64 the lowest steering_angle rounds below -31.374 and would be flagged.
    low = np.array([LIMITS[name][0] for name in SIGNALS], dtype=np.float32)
    high = np.array([LIMITS[name][1] for name in SIGNALS], dtype=np.float32)
    return ~((raw >= low) & (raw <= high)).all(axis=1)
