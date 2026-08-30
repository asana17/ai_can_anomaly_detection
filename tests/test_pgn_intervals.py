from preprocess.frames.can_log_loader import CanFrame
from preprocess.profile.pgn_intervals import arrival_intervals


def _frame(t, can_id):
    return CanFrame(timestamp=t, can_id=can_id, data=b"")


def test_intervals_per_stream():
    # PGN 61444, SA 230 at t = 0, 1, 3 -> gaps 1, 2
    frames = [_frame(0.0, 0x18F004E6), _frame(1.0, 0x18F004E6), _frame(3.0, 0x18F004E6)]
    assert arrival_intervals(frames)[(61444, 230)] == [1.0, 2.0]


def test_streams_separated_by_sender():
    # same PGN, different SA -> separate streams, no cross-sender gap
    frames = [_frame(0.0, 0x18F004E6), _frame(0.5, 0x18F004E7), _frame(2.0, 0x18F004E6)]
    intervals = arrival_intervals(frames)
    assert intervals[(61444, 230)] == [2.0]
    assert (61444, 231) not in intervals  # only one frame from SA 231


def test_single_frame_has_no_interval():
    assert arrival_intervals([_frame(0.0, 0x18F004E6)]) == {}
