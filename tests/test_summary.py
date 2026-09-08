from collections import Counter

from preprocess.profile.summary import (
    GAP_STEP,
    median_gap,
    pgn_gap,
    public_pgns,
    report,
    summarize,
)

EEC1 = 61444        # public, PDU2
PROPRIETARY = 65408  # PDU format 255, so no published SPN definitions


def _can_id(pgn, sender, priority=6):
    return (priority << 26) | (pgn << 8) | sender


def _write_log(path, frames):
    """Write a log from (seconds, pgn, sender, dlc) tuples."""
    lines = ["timestamp;id;dlc;data"]
    for t, pgn, sender, dlc in frames:
        stamp = f"2020-11-23 08:00:{int(t):02d}.{round((t - int(t)) * 1e6):06d}"
        lines.append(f"{stamp};{hex(_can_id(pgn, sender))};{dlc};" + ";".join("0" * dlc))
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def _log(path):
    return _write_log(path, [
        (0.00, EEC1, 230, 8), (0.02, EEC1, 230, 8), (0.04, EEC1, 230, 8),
        (0.00, EEC1, 100, 4), (0.05, EEC1, 100, 4),      # a second, slower sender
        (0.00, PROPRIETARY, 230, 8), (0.10, PROPRIETARY, 230, 8),
    ])


def test_counts_frames_pgns_and_senders(tmp_path):
    p = summarize([_log(tmp_path / "a.csv")])
    assert p.logs == 1 and p.frames == 7
    assert p.pgn_frames == Counter({EEC1: 5, PROPRIETARY: 2})
    assert p.sender_frames == Counter({230: 5, 100: 2})
    assert p.dlc_frames == Counter({8: 5, 4: 2})
    assert p.pgns_per_log == [2]


def test_pgn_logs_counts_logs_not_frames(tmp_path):
    p = summarize([_log(tmp_path / "a.csv"), _log(tmp_path / "b.csv")])
    assert p.logs == 2
    assert p.pgn_logs == Counter({EEC1: 2, PROPRIETARY: 2})   # not 10 and 4


def test_public_pgns_excludes_proprietary(tmp_path):
    p = summarize([_log(tmp_path / "a.csv")])
    assert public_pgns(p) == [EEC1]


def test_median_gap_reads_the_bucketed_counts():
    assert median_gap(Counter({200: 3, 300: 1})) == 200 * GAP_STEP    # 20 ms
    assert median_gap(Counter()) == 0.0


def test_pgn_gap_takes_the_fastest_sender(tmp_path):
    p = summarize([_log(tmp_path / "a.csv")])
    assert pgn_gap(p, EEC1) == 0.02          # 230 sends every 20 ms, 100 every 50 ms
    assert pgn_gap(p, PROPRIETARY) == 0.10


def test_report_leads_with_the_totals(tmp_path):
    lines = report(summarize([_log(tmp_path / "a.csv")])).splitlines()
    assert lines[0] == "1 logs, 7 frames, 2 PGNs"
    assert "public 1 PGNs at 71.4% of frames, proprietary 1 at 28.6%" in lines[2]
    assert any(line.startswith(f"  {EEC1} ") for line in lines)
