"""
Unit tests for the Duration class.

These tests validate initialization, type validation, protobuf serialization
and deserialization round-trip, equality, hashing, string representations,
and immutability for the Duration dataclass.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.duration_pb2 import Duration as proto_Duration


pytestmark = pytest.mark.unit


def test_init_and_attributes():
    """Verify that Duration initializes correctly with an integer seconds value."""
    duration = Duration(seconds=30)
    assert duration.seconds == 30

    zero = Duration(seconds=0)
    assert zero.seconds == 0

    negative = Duration(seconds=-15)
    assert negative.seconds == -15


@pytest.mark.parametrize(
    "invalid_seconds, expected_type",
    [
        (10.5, "float"),
        ("60", "str"),
        (None, "NoneType"),
        ([10], "list"),
        ({"seconds": 10}, "dict"),
    ],
)
def test_init_raises_type_error_for_non_integer(invalid_seconds, expected_type):
    """Verify that initializing Duration with non-integer values raises TypeError."""
    with pytest.raises(TypeError, match=f"seconds must be an integer, got {expected_type}"):
        Duration(seconds=invalid_seconds)


def test_to_proto():
    """Verify conversion from Duration to protobuf Duration."""
    duration = Duration(seconds=120)
    proto = duration._to_proto()

    assert isinstance(proto, proto_Duration)
    assert proto.seconds == 120


def test_from_proto():
    """Verify conversion from protobuf Duration to Duration object."""
    proto = proto_Duration(seconds=3600)
    duration = Duration._from_proto(proto)

    assert isinstance(duration, Duration)
    assert duration.seconds == 3600


def test_from_proto_raises_value_error_for_duration_instance():
    """Verify that passing an existing Duration instance to _from_proto raises ValueError."""
    duration = Duration(seconds=100)
    with pytest.raises(ValueError, match="Invalid duration proto"):
        Duration._from_proto(duration)  # type: ignore[arg-type]


def test_protobuf_round_trip():
    """Verify that a Duration instance can round-trip through protobuf serialization."""
    original = Duration(seconds=7200)
    restored = Duration._from_proto(original._to_proto())

    assert restored == original
    assert restored.seconds == original.seconds


def test_equality_and_hashing():
    """Verify __eq__ and hashing behavior for Duration."""
    d1 = Duration(seconds=60)
    d2 = Duration(seconds=60)
    d3 = Duration(seconds=120)

    assert d1 == d2
    assert d1 != d3
    assert hash(d1) == hash(d2)

    # __eq__ must return False when compared with non-Duration objects
    assert d1 != 60
    assert d1 != "60"
    assert d1 != None  # noqa: E711
    assert d1 != proto_Duration(seconds=60)


def test_string_representations():
    """Verify __str__ and __repr__ output format."""
    duration = Duration(seconds=45)

    assert str(duration) == "Duration of 45 seconds."
    assert repr(duration) == "Duration(seconds=45)"


def test_immutability():
    """Verify that Duration instances are immutable (frozen dataclass)."""
    duration = Duration(seconds=10)
    with pytest.raises(FrozenInstanceError):
        duration.seconds = 20  # type: ignore[misc]
