from __future__ import annotations

import re
import sys

import pytest

from hiero_sdk_python import AccountId, TransactionId


pytestmark = pytest.mark.unit


def test_from_string_valid():
    """Test parsing a valid transaction ID string."""
    tx_id_str = "0.0.123@1234567890.123456789"
    tx_id = TransactionId.from_string(tx_id_str)

    # Protect against breaking changes
    assert isinstance(tx_id, TransactionId)
    assert hasattr(tx_id, "account_id")
    assert hasattr(tx_id, "valid_start")
    assert hasattr(tx_id, "scheduled")

    assert tx_id.account_id == AccountId(0, 0, 123)
    assert tx_id.valid_start.seconds == 1234567890
    assert tx_id.valid_start.nanos == 123456789
    assert tx_id.scheduled is False


def test_from_string_invalid_suffix_raises_error():
    """Test that invalid suffixes raise ValueError."""
    invalid_suffixes = [
        "0.0.123@1234567890.123456789?scheduledxyz",
        "0.0.123@1234567890.123456789?invalid",
        "0.0.123@1234567890.123456789?",
    ]
    for s in invalid_suffixes:
        with pytest.raises(ValueError) as exc_info:
            TransactionId.from_string(s)
        assert "Invalid transaction ID suffix" in str(exc_info.value)


def test_from_string_invalid_format_raises_error():
    """Test that invalid formats raise ValueError (covers the try-except block)."""
    invalid_strings = [
        "invalid_string",
        "0.0.123.123456789",  # Missing @ separator
        "0.0.123@12345",  # Missing . in timestamp
        "0.0.123@abc.def",  # Non-numeric timestamp
    ]

    for s in invalid_strings:
        with pytest.raises(ValueError, match=f"Invalid TransactionId string format: {re.escape(s)}"):
            TransactionId.from_string(s)


INT64_MIN, INT64_MAX = -(2**63), 2**63 - 1
INT32_MIN, INT32_MAX = -(2**31), 2**31 - 1


def test_from_string_scheduled_suffix_still_parses():
    """Test that the '?scheduled' suffix is still accepted."""
    tx_id = TransactionId.from_string("0.0.123@1234567890.500?scheduled")

    assert tx_id.account_id == AccountId(0, 0, 123)
    assert tx_id.valid_start.seconds == 1234567890
    assert tx_id.valid_start.nanos == 500
    assert tx_id.scheduled is True


def test_from_string_unknown_suffix_raises_error():
    """Test that an unknown suffix raises the suffix error, not the generic format error."""
    with pytest.raises(ValueError, match=re.escape("Invalid transaction ID suffix: ?foo")):
        TransactionId.from_string("0.0.123@1234567890.500?foo")


@pytest.mark.parametrize(
    ("tx_id_str", "part"),
    [
        ("0.0.123@abc.500", "seconds 'abc'"),
        ("0.0.123@1234567890.def", "nanos 'def'"),
    ],
)
def test_from_string_non_integer_part_names_the_part(tx_id_str, part):
    """Test that a non-numeric seconds or nanos value is named in the error."""
    with pytest.raises(ValueError) as exc_info:
        TransactionId.from_string(tx_id_str)

    message = str(exc_info.value)
    assert message.startswith(f"Invalid TransactionId string format: {tx_id_str}")
    assert f"{part} is not a valid integer" in message


@pytest.mark.parametrize(
    ("seconds", "nanos", "part"),
    [
        (INT64_MAX + 1, 0, f"seconds {INT64_MAX + 1}"),
        (INT64_MIN - 1, 0, f"seconds {INT64_MIN - 1}"),
        (1234567890, INT32_MAX + 1, f"nanos {INT32_MAX + 1}"),
        (1234567890, INT32_MIN - 1, f"nanos {INT32_MIN - 1}"),
    ],
)
def test_from_string_out_of_range_part_raises_error(seconds, nanos, part):
    """Test that seconds outside int64 and nanos outside int32 raise a ValueError naming the part."""
    tx_id_str = f"0.0.123@{seconds}.{nanos}"

    with pytest.raises(ValueError) as exc_info:
        TransactionId.from_string(tx_id_str)

    message = str(exc_info.value)
    assert message.startswith(f"Invalid TransactionId string format: {tx_id_str}")
    assert f"{part} is out of range" in message


@pytest.mark.parametrize(
    ("seconds", "nanos"),
    [
        (INT64_MAX, 0),
        (INT64_MIN, 0),
        (1234567890, INT32_MAX),
        (1234567890, INT32_MIN),
    ],
)
def test_from_string_accepts_range_limits(seconds, nanos):
    """Test that the int64 and int32 limits themselves are accepted."""
    tx_id = TransactionId.from_string(f"0.0.123@{seconds}.{nanos}")

    assert tx_id.valid_start.seconds == seconds
    assert tx_id.valid_start.nanos == nanos


@pytest.mark.parametrize(
    "tx_id_str",
    [
        "0.0.123@1@2.3",  # More than one @
        "0.0.123@1.2.3",  # More than one . in the timestamp
        "not-an-account@1234567890.500",  # Invalid account ID
        "0.0.ff@1234567890.500",  # Invalid alias account ID
    ],
)
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_from_string_other_invalid_formats_keep_generic_message(tx_id_str):
    """Test that other malformed strings still raise the generic format error."""
    with pytest.raises(ValueError, match=f"^Invalid TransactionId string format: {re.escape(tx_id_str)}$"):
        TransactionId.from_string(tx_id_str)


@pytest.mark.filterwarnings("error::UserWarning")
def test_from_string_invalid_alias_with_warnings_as_errors_raises_value_error():
    """Test that a warning raised as an error while parsing the account ID still becomes a ValueError."""
    tx_id_str = "0.0.ff@1234567890.500"

    with pytest.raises(ValueError, match=f"^Invalid TransactionId string format: {re.escape(tx_id_str)}$"):
        TransactionId.from_string(tx_id_str)


@pytest.mark.parametrize("value", [None, 123, b"0.0.123@1234567890.500"])
def test_from_string_non_string_raises_value_error(value):
    """Test that a non-string input raises the generic format error, not a TypeError."""
    with pytest.raises(ValueError, match="^Invalid TransactionId string format: "):
        TransactionId.from_string(value)


@pytest.fixture
def int_max_str_digits():
    """Set Python's integer string conversion limit to its default (4300) for one test."""
    previous = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(4300)
    yield
    sys.set_int_max_str_digits(previous)


@pytest.mark.usefixtures("int_max_str_digits")
def test_from_string_very_long_seconds_is_out_of_range():
    """Test that seconds too long for int() are reported as out of range, not as non-integers."""
    tx_id_str = "0.0.123@" + "9" * 5000 + ".500"

    with pytest.raises(ValueError, match="seconds is out of range"):
        TransactionId.from_string(tx_id_str)


@pytest.mark.usefixtures("int_max_str_digits")
def test_from_string_very_long_grouped_seconds_is_out_of_range():
    """Test that a very long integer with underscores, which int() accepts, is reported as out of range."""
    tx_id_str = "0.0.123@" + "_".join(["999"] * 2000) + ".500"

    with pytest.raises(ValueError, match="seconds is out of range"):
        TransactionId.from_string(tx_id_str)


@pytest.mark.usefixtures("int_max_str_digits")
@pytest.mark.parametrize(
    "seconds",
    [
        "++1",  # Two signs
        "+-" + "9" * 5000,  # Two signs, too long for int()
        "9" * 5000 + "x",  # Too long for int(), and not an integer
    ],
)
def test_from_string_malformed_seconds_is_not_a_valid_integer(seconds):
    """Test that malformed seconds are reported as not a valid integer, even when very long."""
    with pytest.raises(ValueError, match="seconds .* is not a valid integer"):
        TransactionId.from_string(f"0.0.123@{seconds}.500")


def test_hash_implementation():
    """Test __hash__ implementation coverage."""
    tx_id1 = TransactionId.from_string("0.0.1@100.1")
    tx_id2 = TransactionId.from_string("0.0.1@100.1")
    tx_id3 = TransactionId.from_string("0.0.2@100.1")

    # Hashes should be equal for equal objects
    assert hash(tx_id1) == hash(tx_id2)
    # Hashes should typically differ for different objects
    assert hash(tx_id1) != hash(tx_id3)

    # Verify usage in sets
    unique_ids = {tx_id1, tx_id2, tx_id3}
    assert len(unique_ids) == 2
    tx_id4 = TransactionId.from_string("0.0.1@100.1")
    tx_id5 = TransactionId.from_string("0.0.1@100.1")
    tx_id5.scheduled = True

    assert hash(tx_id4) != hash(tx_id5), "Hash should differ when scheduled flag differs"


def test_equality():
    """Test __eq__ implementation."""
    tx_id1 = TransactionId.from_string("0.0.1@100.1")
    tx_id2 = TransactionId.from_string("0.0.1@100.1")

    assert tx_id1 == tx_id2
    assert tx_id1 != "some_string"
    assert tx_id1 != TransactionId.from_string("0.0.1@100.2")

    tx_id4 = TransactionId.from_string("0.0.1@100.1")
    tx_id5 = TransactionId.from_string("0.0.1@100.1")
    tx_id5.scheduled = True

    assert tx_id4 != tx_id5, "TransactionIds with different scheduled flags should not be equal"


def test_to_proto_sets_scheduled():
    """Test that _to_proto sets the scheduled flag correctly."""
    tx_id = TransactionId.from_string("0.0.123@100.1")

    # Default is False
    proto_default = tx_id._to_proto()
    assert proto_default.scheduled is False

    # Set to True
    tx_id.scheduled = True
    proto_scheduled = tx_id._to_proto()
    assert proto_scheduled.scheduled is True


def test_generate():
    """Test generating a new TransactionId."""
    account_id = AccountId(0, 0, 123)
    tx_id = TransactionId.generate(account_id)

    # Protect against breaking changes
    assert isinstance(tx_id, TransactionId)
    assert hasattr(tx_id, "account_id")
    assert hasattr(tx_id, "valid_start")
    assert hasattr(tx_id, "scheduled")

    assert tx_id.account_id == account_id
    assert tx_id.valid_start is not None
    assert tx_id.valid_start.seconds > 0
    assert tx_id.valid_start.nanos >= 0
    assert tx_id.scheduled is False, "Generated TransactionId should have scheduled=False by default"


def test_to_string():
    """Test converting TransactionId to string."""
    tx_id = TransactionId.from_string("0.0.123@1234567890.123456789")
    result = tx_id.to_string()

    assert isinstance(result, str)
    assert result == "0.0.123@1234567890.123456789"

    # Test with scheduled flag
    tx_id.scheduled = True
    result_scheduled = tx_id.to_string()
    assert "?scheduled" in result_scheduled


def test_str_method():
    """Test __str__ returns the same as to_string()."""
    tx_id = TransactionId.from_string("0.0.123@1234567890.123456789")

    assert str(tx_id) == tx_id.to_string()


def test_from_proto():
    """Test creating TransactionId from protobuf."""
    # Create a TransactionId and convert to proto
    original = TransactionId.from_string("0.0.123@1234567890.123456789")
    original.scheduled = True
    proto = original._to_proto()

    # Create from proto and verify all fields
    from_proto = TransactionId._from_proto(proto)

    assert isinstance(from_proto, TransactionId)
    assert from_proto.account_id == original.account_id
    assert from_proto.valid_start.seconds == original.valid_start.seconds
    assert from_proto.valid_start.nanos == original.valid_start.nanos
    assert from_proto.scheduled == original.scheduled


def test_round_trip_conversion():
    """Test that to_proto -> from_proto preserves all data."""
    original = TransactionId.from_string("0.0.999@9876543210.987654321")
    original.scheduled = True

    proto = original._to_proto()
    recovered = TransactionId._from_proto(proto)

    assert recovered == original
    assert recovered.to_string() == original.to_string()


def test_from_string_with_scheduled_flag():
    """Test parsing a transaction ID string with scheduled flag."""
    tx_id = TransactionId.from_string("0.0.123@1234567890.123456789?scheduled")

    assert isinstance(tx_id, TransactionId)
    assert tx_id.account_id == AccountId(0, 0, 123)
    assert tx_id.valid_start.seconds == 1234567890
    assert tx_id.valid_start.nanos == 123456789
    assert tx_id.scheduled is True
