from attack.replay.replay import replay

from can_frames import CCVS1, EEC1, speed_frame, rpm_frame


def _trace():
    # speed climbs 0, 10, 20, 30 while the engine holds, one frame of each per second
    return [f for t in range(4)
            for f in (speed_frame(float(t), t * 10.0), rpm_frame(float(t), 800.0))]


def test_the_window_takes_the_payload_from_the_source_time():
    out = replay(_trace(), [65265], start=3.0, stop=3.0, source=0.0)
    # 30 km/h replaced by the 0 km/h bytes
    assert out[-2].data == speed_frame(0.0, 0.0).data


def test_times_and_count_do_not_change():
    trace = _trace()
    out = replay(trace, [65265], start=1.0, stop=3.0, source=0.0)
    assert [f.timestamp for f in out] == [f.timestamp for f in trace]
    assert [f.can_id for f in out] == [f.can_id for f in trace]


def test_frames_outside_the_window_are_untouched():
    trace = _trace()
    out = replay(trace, [65265], start=3.0, stop=3.0, source=0.0)
    assert out[0].data == trace[0].data
    assert out[2].data == trace[2].data


def test_a_pgn_not_named_is_untouched():
    trace = _trace()
    out = replay(trace, [65265], start=0.0, stop=3.0, source=0.0)
    assert [f.data for f in out if f.can_id == EEC1] == [f.data for f in trace if f.can_id == EEC1]


def test_the_window_walks_the_source_at_the_same_pace():
    out = replay(_trace(), [65265], start=2.0, stop=3.0, source=0.0)
    speeds = [f.data for f in out if f.can_id == CCVS1]
    assert speeds[2:] == [speed_frame(0.0, 0.0).data, speed_frame(0.0, 10.0).data]


def test_naming_a_pgn_the_trace_does_not_carry_changes_nothing():
    trace = _trace()
    assert replay(trace, [61449], start=0.0, stop=3.0, source=0.0) == trace


def test_repeat_seconds_goes_back_to_the_source():
    out = replay(_trace(), [65265], start=1.0, stop=3.0, source=0.0, repeat_seconds=1.0)
    speeds = [f.data for f in out if f.can_id == CCVS1]
    assert speeds[1:] == [speed_frame(0.0, 0.0).data] * 3


def test_repeat_seconds_of_zero_holds_the_source():
    out = replay(_trace(), [65265], start=1.0, stop=3.0, source=1.0, repeat_seconds=0.0)
    speeds = [f.data for f in out if f.can_id == CCVS1]
    assert speeds[1:] == [speed_frame(0.0, 10.0).data] * 3
