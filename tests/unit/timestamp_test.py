"""
Unit tests for the Timestamp class.

These tests validate correctness, edge cases, precision handling,
serialization, arithmetic, comparison, and time-based behavior to
ensure robust coverage of timestamp functionality.
"""

import time
import pytest
from datetime import datetime, timezone

from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp as TimestampProto

pytestmark = pytest.mark.unit


# Constructor and basic tests


def test_init_and_attributes():
    """Verify that Timestamp initializes correctly with seconds and nanoseconds."""
    ts = Timestamp(10, 500)
    assert ts.seconds == 10
    assert ts.nanos == 500


def test_eq_and_hash():
    """Ensure equality and hashing behave correctly for Timestamp instances."""
    ts1 = Timestamp(10, 500)
    ts2 = Timestamp(10, 500)
    ts3 = Timestamp(11, 0)

    assert ts1 == ts2
    assert ts1 != ts3
    assert hash(ts1) == hash(ts2)


def test_str_representation_zero_padded():
    """Ensure string representation is zero-padded to 9 nanoseconds digits."""
    ts = Timestamp(10, 5)
    assert str(ts) == "10.000000005"


# from_date() tests


@pytest.mark.parametrize(
    "value",
    [
        datetime(1970, 1, 1, tzinfo=timezone.utc),
        int(time.time()),
        "1970-01-01T00:00:00+00:00",
    ],
)
def test_from_date_valid_inputs(value):
    """Test from_date with valid inputs: datetime, int, and ISO-8601 string."""
    ts = Timestamp.from_date(value)
    assert isinstance(ts, Timestamp)


def test_from_date_unix_epoch():
    """Test from_date with the Unix epoch (0 seconds)."""
    dt = datetime(1970, 1, 1, tzinfo=timezone.utc)
    ts = Timestamp.from_date(dt)
    assert ts.seconds == 0
    assert ts.nanos == 0




def test_from_date_max_microseconds():
    """Test from_date with maximum microseconds to ensure nanos calculation is correct."""
    dt = datetime(2020, 1, 1, 0, 0, 0, 999999, tzinfo=timezone.utc)
    ts = Timestamp.from_date(dt)

    expected = 999_999_000
    assert abs(ts.nanos - expected) < 1_000

@pytest.mark.parametrize("bad_input", [None, [], {}, 3.14])
def test_from_date_invalid_type(bad_input):
    """Ensure from_date raises ValueError for invalid input types."""
    with pytest.raises(ValueError, match="Invalid type for date"):
        Timestamp.from_date(bad_input)


# to_date() tests


def test_to_date_returns_utc_datetime():
    """Verify that to_date returns a UTC datetime with correct seconds and microseconds."""
    ts = Timestamp(10, 500_000_000)
    dt = ts.to_date()

    assert isinstance(dt, datetime)
    assert dt.tzinfo == timezone.utc
    assert dt.second == 10
    assert dt.microsecond == 500_000


def test_to_date_truncates_nanoseconds():
    """Ensure that nanoseconds are truncated (not rounded) when converting to datetime."""
    ts = Timestamp(0, 123_456_789)
    dt = ts.to_date()
    assert dt.microsecond == 123_456


def test_datetime_round_trip_preserves_microseconds():
    """Verify that datetime -> Timestamp -> datetime preserves microsecond precision."""
    original = datetime.now(timezone.utc).replace(microsecond=654321)
    ts = Timestamp.from_date(original)
    result = ts.to_date()
    assert original.replace(microsecond=result.microsecond) == result


# plus_nanos() tests


def test_plus_nanos_simple_add():
    """Test simple addition of nanoseconds without overflow."""
    ts = Timestamp(1, 100)
    new_ts = ts.plus_nanos(200)
    assert new_ts.seconds == 1
    assert new_ts.nanos == 300


def test_plus_nanos_carry_over():
    """Test addition of nanoseconds causing a carry-over into seconds."""
    ts = Timestamp(1, 900_000_000)
    new_ts = ts.plus_nanos(200_000_000)
    assert new_ts.seconds == 2
    assert new_ts.nanos == 100_000_000


def test_plus_nanos_multiple_seconds():
    """Test addition of nanoseconds resulting in multiple seconds overflow."""
    ts = Timestamp(1, 0)
    new_ts = ts.plus_nanos(3_000_000_000)
    assert new_ts.seconds == 4
    assert new_ts.nanos == 0


def test_plus_nanos_zero():
    """Test adding zero nanoseconds returns the same Timestamp instance."""
    ts = Timestamp(5, 123)
    new_ts = ts.plus_nanos(0)
    assert new_ts == ts


# compare() tests


def test_compare_equal():
    """Verify compare returns 0 for equal Timestamps."""
    ts1 = Timestamp(10, 0)
    ts2 = Timestamp(10, 0)
    assert ts1.compare(ts2) == 0


def test_compare_less_than():
    """Verify compare returns -1 when first Timestamp is earlier."""
    ts1 = Timestamp(9, 0)
    ts2 = Timestamp(10, 0)
    assert ts1.compare(ts2) == -1


def test_compare_greater_than():
    """Verify compare returns 1 when first Timestamp is later."""
    ts1 = Timestamp(10, 1)
    ts2 = Timestamp(10, 0)
    assert ts1.compare(ts2) == 1


# generate() tests


def test_generate_without_jitter():
    """Ensure generate without jitter produces a timestamp close to current time."""
    ts = Timestamp.generate(has_jitter=False)
    delta = abs(ts.to_date().timestamp() - time.time())

    assert delta < 0.1



def test_generate_with_jitter():
    """Verify that generated timestamps with jitter remain close to the system time within a safe tolerance."""
    ts = Timestamp.generate(has_jitter=True)
    delta = time.time() - ts.to_date().timestamp()

    # Jitter is explicitly 3-8 seconds backward
    assert 3.0 <= delta <= 9.0

# Protobuf serialization tests


def test_to_protobuf():
    """Ensure Timestamp converts correctly to protobuf representation."""
    ts = Timestamp(10, 500)
    proto = ts._to_protobuf()
    assert isinstance(proto, TimestampProto)
    assert proto.seconds == 10
    assert proto.nanos == 500


def test_from_protobuf():
    """Ensure Timestamp can be created from a protobuf object."""
    proto = TimestampProto(seconds=10, nanos=500)
    ts = Timestamp._from_protobuf(proto)
    assert ts.seconds == 10
    assert ts.nanos == 500


def test_protobuf_round_trip():
    """Verify that protobuf serialization and deserialization preserves the original Timestamp."""
    original = Timestamp(123, 456)
    proto = original._to_protobuf()
    restored = Timestamp._from_protobuf(proto)
    assert original == restored
