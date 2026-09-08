"""Fold a set of logs into the counts that describe the dataset.

This is how the profiling findings in [measurements](../../dataset/measurements.md)
were measured, so they can be checked or remeasured on any set of files.
"""

from __future__ import annotations

import sys
from collections import Counter
from typing import Iterable

from preprocess.frames.can_log_loader import load_can_log
from preprocess.profile.pgn_classify import is_proprietary_pgn
from preprocess.profile.pgn_counts import count_pgn_senders, count_pgns
from preprocess.profile.pgn_intervals import arrival_intervals

# Arrival gaps are bucketed rather than kept, so millions of frames stay in bounded
# memory. A periodic message lands in a few buckets.
GAP_STEP = 0.0001


class Profile:
    def __init__(self):
        self.logs = 0
        self.frames = 0
        self.pgn_frames = Counter()     # frames per PGN
        self.pgn_logs = Counter()       # logs each PGN appears in
        self.sender_frames = Counter()  # frames per source address
        self.dlc_frames = Counter()     # frames per payload length
        self.pgns_per_log = []          # distinct PGNs in each log
        self.gaps = {}                  # (PGN, sender) -> gaps in GAP_STEP units

    def add(self, log: list) -> None:
        """Fold one log's frames into the counts."""
        counts = count_pgns(log)
        self.logs += 1
        self.frames += len(log)
        self.pgn_frames.update(counts)
        self.pgn_logs.update(counts.keys())
        self.pgns_per_log.append(len(counts))
        self.dlc_frames.update(len(f.data) for f in log)
        self._add_senders(log)
        self._add_gaps(log)

    def _add_senders(self, log: list) -> None:
        for senders in count_pgn_senders(log).values():
            self.sender_frames.update(senders)

    def _add_gaps(self, log: list) -> None:
        for stream, gaps in arrival_intervals(log).items():
            bucket = self.gaps.setdefault(stream, Counter())
            bucket.update(round(gap / GAP_STEP) for gap in gaps)


def summarize(paths: Iterable[str]) -> Profile:
    """Fold every log in `paths` into one Profile."""
    profile = Profile()
    for path in paths:
        profile.add(list(load_can_log(path)))   # read once, then walk it a few times
    return profile


def median_gap(bucket: Counter) -> float:
    """The median arrival gap of one stream, in seconds."""
    seen = 0
    half = sum(bucket.values()) / 2
    for step in sorted(bucket):
        seen += bucket[step]
        if seen >= half:
            return step * GAP_STEP
    return 0.0


def pgn_gap(profile: Profile, pgn: int) -> float:
    """The median gap of the fastest sender of `pgn`, in seconds."""
    buckets = [b for (p, _), b in profile.gaps.items() if p == pgn]
    return min((median_gap(b) for b in buckets), default=0.0)


def public_pgns(profile: Profile) -> list:
    """The PGNs with published SPN definitions, so the ones that can be decoded."""
    return [pgn for pgn in profile.pgn_frames if not is_proprietary_pgn(pgn)]


def report(profile: Profile) -> str:
    """Render a profile as totals followed by a row per PGN."""
    return "\n".join(_totals(profile) + [""] + _table(profile))


def _shares(counts: Counter, total: int, limit: int) -> str:
    return ", ".join(f"{k} {100 * c / total:.2f}%" for k, c in counts.most_common(limit))


def _totals(profile: Profile) -> list[str]:
    per_log = sorted(profile.pgns_per_log)
    public = sum(profile.pgn_frames[pgn] for pgn in public_pgns(profile))
    everywhere = sum(1 for p, n in profile.pgn_logs.items() if n == profile.logs)
    return [
        f"{profile.logs} logs, {profile.frames:,} frames, {len(profile.pgn_frames)} PGNs",
        f"per log {per_log[0]} to {per_log[-1]} PGNs, median "
        f"{per_log[len(per_log) // 2]}, {everywhere} in every log",
        f"public {len(public_pgns(profile))} PGNs at {100 * public / profile.frames:.1f}% "
        f"of frames, proprietary {len(profile.pgn_frames) - len(public_pgns(profile))} at "
        f"{100 * (profile.frames - public) / profile.frames:.1f}%",
        f"dlc {_shares(profile.dlc_frames, profile.frames, 6)}",
        f"senders {_shares(profile.sender_frames, profile.frames, 6)}",
    ]


def _table(profile: Profile) -> list[str]:
    rows = [f"{'PGN':>7} {'hex':>7} {'frames':>8} {'logs':>7} {'gap':>9}  kind"]
    for pgn, count in profile.pgn_frames.most_common():
        kind = "proprietary" if is_proprietary_pgn(pgn) else "public"
        rows.append(
            f"{pgn:>7} {hex(pgn):>7} {100 * count / profile.frames:>7.3f}% "
            f"{100 * profile.pgn_logs[pgn] / profile.logs:>6.0f}% "
            f"{1000 * pgn_gap(profile, pgn):>7.1f}ms  {kind}"
        )
    return rows


if __name__ == "__main__":
    print(report(summarize(sys.argv[1:])))
