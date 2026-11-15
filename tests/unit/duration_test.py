"""Unit tests for the Duration class."""

from __future__ import annotations

import pytest

from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.duration_pb2 import Duration as proto_Duration


pytestmark = pytest.mark.unit


def test_init_sets_seconds():
    assert Duration(seconds=5).seconds == 5


def test_init_zero_seconds():
    assert Duration(seconds=0).seconds == 0


def test_init_negative_seconds():
    assert Duration(seconds=-7).seconds == -7


def test_init_rejects_non_int_seconds():
    with pytest.raises(TypeError):
        Duration(seconds="5")  # type: ignore[arg-type]


def test_eq_returns_false_for_non_duration():
    assert (Duration(seconds=5) == "Not a Duration") is False
    assert Duration(seconds=5) != "Not a Duration"


def test_eq_true_for_matching_duration():
    assert Duration(seconds=5) == Duration(seconds=5)


def test_eq_false_for_different_seconds():
    assert Duration(seconds=5) != Duration(seconds=6)


def test_to_proto_returns_proto_duration_with_seconds():
    proto = Duration(seconds=42)._to_proto()
    assert isinstance(proto, proto_Duration)
    assert proto.seconds == 42


def test_from_proto_builds_duration_from_proto():
    proto = proto_Duration(seconds=123)
    duration = Duration._from_proto(proto)
    assert duration == Duration(seconds=123)


def test_from_proto_round_trip():
    original = Duration(seconds=99)
    assert Duration._from_proto(original._to_proto()) == original


def test_from_proto_raises_value_error_on_duration_instance():
    with pytest.raises(ValueError):
        Duration._from_proto(Duration(seconds=1))  # type: ignore[arg-type]


def test_str():
    assert str(Duration(seconds=5)) == "Duration of 5 seconds."
    assert str(Duration(seconds=0)) == "Duration of 0 seconds."
    assert str(Duration(seconds=-7)) == "Duration of -7 seconds."


def test_repr():
    assert repr(Duration(seconds=5)) == "Duration(seconds=5)"
    assert repr(Duration(seconds=0)) == "Duration(seconds=0)"
    assert repr(Duration(seconds=-7)) == "Duration(seconds=-7)"
