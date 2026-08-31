from preprocess.features.signal_state import SIGNALS, SignalState


def test_holds_latest_value_per_signal():
    s = SignalState()
    s.update({"engine_speed": 1000.0})
    s.update({"engine_speed": 1200.0})
    assert s.snapshot()[SIGNALS.index("engine_speed")] == 1200.0


def test_unknown_signal_is_ignored():
    s = SignalState()
    s.update({"not_a_signal": 5.0})
    assert all(v is None for v in s.snapshot())


def test_ready_only_when_all_signals_seen():
    s = SignalState()
    assert not s.ready()
    for name in SIGNALS:
        s.update({name: 1.0})
    assert s.ready()
    assert s.snapshot() == [1.0] * len(SIGNALS)


def test_signals_come_from_spec():
    assert "engine_speed" in SIGNALS
    assert "wheel_speed" in SIGNALS
    assert len(SIGNALS) == 7
