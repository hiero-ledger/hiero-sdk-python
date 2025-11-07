"""
Test cases for the FreezeType enum class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.hapi.services.freeze_type_pb2 import (
    FreezeType as proto_FreezeType,
)
from hiero_sdk_python.system.freeze_type import FreezeType

pytestmark = pytest.mark.unit


def test_freeze_type_values():
    """Test that FreezeType enum has correct values."""
    assert FreezeType.UNKNOWN_FREEZE_TYPE.value == 0
    assert FreezeType.FREEZE_ONLY.value == 1
    assert FreezeType.PREPARE_UPGRADE.value == 2
    assert FreezeType.FREEZE_UPGRADE.value == 3
    assert FreezeType.FREEZE_ABORT.value == 4
    assert FreezeType.TELEMETRY_UPGRADE.value == 5


def test_from_proto_all_types():
    """Test _from_proto method with all freeze types."""
    test_cases = [
        (proto_FreezeType.FREEZE_ONLY, FreezeType.FREEZE_ONLY),
        (proto_FreezeType.PREPARE_UPGRADE, FreezeType.PREPARE_UPGRADE),
        (proto_FreezeType.FREEZE_UPGRADE, FreezeType.FREEZE_UPGRADE),
        (proto_FreezeType.FREEZE_ABORT, FreezeType.FREEZE_ABORT),
        (proto_FreezeType.TELEMETRY_UPGRADE, FreezeType.TELEMETRY_UPGRADE),
        (proto_FreezeType.UNKNOWN_FREEZE_TYPE, FreezeType.UNKNOWN_FREEZE_TYPE),
    ]

    for proto_type, expected in test_cases:
        result = FreezeType._from_proto(proto_type)
        assert result == expected


def test_from_proto_invalid_value():
    """Test _from_proto method with invalid proto value returns UNKNOWN_FREEZE_TYPE."""
    mock_proto = MagicMock()
    mock_proto.__eq__ = lambda self, other: False

    result = FreezeType._from_proto(mock_proto)
    assert result == FreezeType.UNKNOWN_FREEZE_TYPE


def test_to_proto_all_types():
    """Test _to_proto method with all freeze types."""
    test_cases = [
        (FreezeType.FREEZE_ONLY, proto_FreezeType.FREEZE_ONLY),
        (FreezeType.PREPARE_UPGRADE, proto_FreezeType.PREPARE_UPGRADE),
        (FreezeType.FREEZE_UPGRADE, proto_FreezeType.FREEZE_UPGRADE),
        (FreezeType.FREEZE_ABORT, proto_FreezeType.FREEZE_ABORT),
        (FreezeType.TELEMETRY_UPGRADE, proto_FreezeType.TELEMETRY_UPGRADE),
        (FreezeType.UNKNOWN_FREEZE_TYPE, proto_FreezeType.UNKNOWN_FREEZE_TYPE),
    ]

    for freeze_type, expected in test_cases:
        proto_result = freeze_type._to_proto()
        assert proto_result == expected


def test_eq():
    """Test __eq__ method for FreezeType."""
    assert FreezeType.FREEZE_ONLY == FreezeType.FREEZE_ONLY
    assert FreezeType.FREEZE_ONLY != FreezeType.PREPARE_UPGRADE

    assert FreezeType.FREEZE_ONLY == 1
    assert FreezeType.PREPARE_UPGRADE == 2
    assert FreezeType.FREEZE_ONLY != 0

    assert FreezeType.FREEZE_ONLY != "FREEZE_ONLY"
    assert FreezeType.FREEZE_ONLY is not None


def test_round_trip_conversion():
    """Test round-trip conversion from FreezeType to proto and back."""
    freeze_types = [
        FreezeType.UNKNOWN_FREEZE_TYPE,
        FreezeType.FREEZE_ONLY,
        FreezeType.PREPARE_UPGRADE,
        FreezeType.FREEZE_UPGRADE,
        FreezeType.FREEZE_ABORT,
        FreezeType.TELEMETRY_UPGRADE,
    ]

    for freeze_type in freeze_types:
        proto_obj = freeze_type._to_proto()
        converted_back = FreezeType._from_proto(proto_obj)
        assert converted_back == freeze_type
