"""Flag any signal that falls outside the range J1939 defines for it."""

from __future__ import annotations

from preprocess.frames.spn_spec import SPEC

LIMITS = {d.name: (d.minimum, d.maximum) for defs in SPEC.values() for d in defs}


def violations(values: dict) -> list:
    """The names in `values` that sit outside their range, in the order given."""
    out = []
    for name, value in values.items():
        limits = LIMITS.get(name)
        if limits and not limits[0] <= value <= limits[1]:
            out.append(name)
    return out
