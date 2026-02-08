"""Tests for the StakingInfo class."""

import pytest
from dataclasses import FrozenInstanceError

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.basic_types_pb2 import (
    StakingInfo as StakingInfoProto,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.staking_info import StakingInfo
from hiero_sdk_python.timestamp import Timestamp

pytestmark = pytest.mark.unit


@pytest.fixture(name="staking_info_with_account")
def fixture_staking_info_with_account():
    """Return a StakingInfo instance staked to an account."""
    return StakingInfo(
        decline_reward=True,
        stake_period_start=Timestamp(100, 200),
        pending_reward=Hbar.from_tinybars(1234),
        staked_to_me=Hbar.from_tinybars(5678),
        staked_account_id=AccountId(0, 0, 123),
    )


@pytest.fixture(name="staking_info_with_node")
def fixture_staking_info_with_node():
    """Return a StakingInfo instance staked to a node."""
    return StakingInfo(
        decline_reward=False,
        stake_period_start=Timestamp(300, 400),
        pending_reward=Hbar.from_tinybars(2222),
        staked_to_me=Hbar.from_tinybars(4444),
        staked_node_id=3,
    )


@pytest.fixture(name="proto_staking_info_with_account")
def fixture_proto_staking_info_with_account():
    """Return a StakingInfo protobuf staked to an account."""
    return StakingInfoProto(
        decline_reward=True,
        stake_period_start=Timestamp(100, 200)._to_protobuf(),
        pending_reward=1234,
        staked_to_me=5678,
        staked_account_id=AccountId(0, 0, 123)._to_proto(),
    )


@pytest.fixture(name="proto_staking_info_with_node")
def fixture_proto_staking_info_with_node():
    """Return a StakingInfo protobuf staked to a node."""
    return StakingInfoProto(
        decline_reward=False,
        stake_period_start=Timestamp(300, 400)._to_protobuf(),
        pending_reward=2222,
        staked_to_me=4444,
        staked_node_id=3,
    )


def test_default_initialization():
    """Verify defaults for an empty StakingInfo."""
    staking_info = StakingInfo()

    assert staking_info.decline_reward is None
    assert staking_info.stake_period_start is None
    assert staking_info.pending_reward is None
    assert staking_info.staked_to_me is None
    assert staking_info.staked_account_id is None
    assert staking_info.staked_node_id is None


def test_frozen_instance_is_immutable():
    """Ensure dataclass is frozen and rejects mutation."""
    staking_info = StakingInfo()
    with pytest.raises(FrozenInstanceError):
        staking_info.decline_reward = True


def test_initialization_with_account(staking_info_with_account):
    """Validate field values when staked to an account."""
    staking_info = staking_info_with_account

    assert staking_info.decline_reward is True
    assert staking_info.stake_period_start == Timestamp(100, 200)
    assert staking_info.pending_reward == Hbar.from_tinybars(1234)
    assert staking_info.staked_to_me == Hbar.from_tinybars(5678)
    assert str(staking_info.staked_account_id) == "0.0.123"
    assert staking_info.staked_node_id is None


def test_initialization_with_node(staking_info_with_node):
    """Validate field values when staked to a node."""
    staking_info = staking_info_with_node

    assert staking_info.decline_reward is False
    assert staking_info.stake_period_start == Timestamp(300, 400)
    assert staking_info.pending_reward == Hbar.from_tinybars(2222)
    assert staking_info.staked_to_me == Hbar.from_tinybars(4444)
    assert staking_info.staked_account_id is None
    assert staking_info.staked_node_id == 3


def test_oneof_validation_raises():
    """Reject setting both staked_account_id and staked_node_id."""
    with pytest.raises(
        ValueError,
        match=r"Only one of staked_account_id or staked_node_id can be set\.",
    ):
        StakingInfo(
            staked_account_id=AccountId(0, 0, 123),
            staked_node_id=3,
        )


def test_from_proto_with_account(proto_staking_info_with_account):
    """Build StakingInfo from a proto with an account target."""
    staking_info = StakingInfo._from_proto(proto_staking_info_with_account)

    assert staking_info.decline_reward is True
    assert staking_info.stake_period_start == Timestamp(100, 200)
    assert staking_info.pending_reward == Hbar.from_tinybars(1234)
    assert staking_info.staked_to_me == Hbar.from_tinybars(5678)
    assert str(staking_info.staked_account_id) == "0.0.123"
    assert staking_info.staked_node_id is None


def test_from_proto_with_node(proto_staking_info_with_node):
    """Build StakingInfo from a proto with a node target."""
    staking_info = StakingInfo._from_proto(proto_staking_info_with_node)

    assert staking_info.decline_reward is False
    assert staking_info.stake_period_start == Timestamp(300, 400)
    assert staking_info.pending_reward == Hbar.from_tinybars(2222)
    assert staking_info.staked_to_me == Hbar.from_tinybars(4444)
    assert staking_info.staked_account_id is None
    assert staking_info.staked_node_id == 3


def test_from_proto_none_raises():
    """Reject None inputs when building from proto."""
    with pytest.raises(ValueError, match=r"Staking info proto is None"):
        StakingInfo._from_proto(None)


def test_to_proto_with_account(staking_info_with_account):
    """Serialize to proto when staked to an account."""
    proto = staking_info_with_account._to_proto()

    assert proto.decline_reward is True
    assert proto.HasField("stake_period_start")
    assert proto.stake_period_start == Timestamp(100, 200)._to_protobuf()
    assert proto.pending_reward == 1234
    assert proto.staked_to_me == 5678
    assert proto.HasField("staked_account_id")
    assert proto.staked_account_id == AccountId(0, 0, 123)._to_proto()
    assert not proto.HasField("staked_node_id")


def test_to_proto_with_node(staking_info_with_node):
    """Serialize to proto when staked to a node."""
    proto = staking_info_with_node._to_proto()

    assert proto.decline_reward is False
    assert proto.HasField("stake_period_start")
    assert proto.stake_period_start == Timestamp(300, 400)._to_protobuf()
    assert proto.pending_reward == 2222
    assert proto.staked_to_me == 4444
    assert not proto.HasField("staked_account_id")
    assert proto.HasField("staked_node_id")
    assert proto.staked_node_id == 3


def test_proto_round_trip_with_account(staking_info_with_account):
    """Round-trip proto serialization with an account target."""
    restored = StakingInfo._from_proto(staking_info_with_account._to_proto())

    assert restored.decline_reward == staking_info_with_account.decline_reward
    assert restored.stake_period_start == staking_info_with_account.stake_period_start
    assert restored.pending_reward == staking_info_with_account.pending_reward
    assert restored.staked_to_me == staking_info_with_account.staked_to_me
    assert str(restored.staked_account_id) == str(
        staking_info_with_account.staked_account_id
    )
    assert restored.staked_node_id is None


def test_proto_round_trip_with_node(staking_info_with_node):
    """Round-trip proto serialization with a node target."""
    restored = StakingInfo._from_proto(staking_info_with_node._to_proto())

    assert restored.decline_reward == staking_info_with_node.decline_reward
    assert restored.stake_period_start == staking_info_with_node.stake_period_start
    assert restored.pending_reward == staking_info_with_node.pending_reward
    assert restored.staked_to_me == staking_info_with_node.staked_to_me
    assert restored.staked_account_id is None
    assert restored.staked_node_id == staking_info_with_node.staked_node_id


def test_from_bytes_deserializes(staking_info_with_account):
    """Deserialize from bytes into an equivalent StakingInfo."""
    data = staking_info_with_account.to_bytes()
    restored = StakingInfo.from_bytes(data)

    assert restored.decline_reward == staking_info_with_account.decline_reward
    assert restored.stake_period_start == staking_info_with_account.stake_period_start
    assert restored.pending_reward == staking_info_with_account.pending_reward
    assert restored.staked_to_me == staking_info_with_account.staked_to_me
    assert str(restored.staked_account_id) == str(
        staking_info_with_account.staked_account_id
    )
    assert restored.staked_node_id is None


def test_from_bytes_empty_raises():
    """Reject empty byte payloads."""
    with pytest.raises(ValueError, match=r"data cannot be empty"):
        StakingInfo.from_bytes(b"")


def test_from_bytes_with_string_raises():
    """Reject non-bytes payloads of type str."""
    with pytest.raises(TypeError, match=r"data must be bytes"):
        StakingInfo.from_bytes("Hi from Anto :D")


def test_from_bytes_with_int_raises():
    """Reject non-bytes payloads of type int."""
    with pytest.raises(TypeError, match=r"data must be bytes"):
        StakingInfo.from_bytes(123)


def test_from_bytes_invalid_bytes_raises():
    """Reject malformed byte payloads."""
    with pytest.raises(ValueError, match=r"Failed to parse StakingInfo bytes"):
        StakingInfo.from_bytes(b"\xff\xff\xff")


def test_to_bytes_produces_non_empty_bytes(staking_info_with_node):
    """Ensure serialization yields a non-empty bytes payload."""
    data = staking_info_with_node.to_bytes()

    assert isinstance(data, bytes)
    assert len(data) > 0


def test_bytes_round_trip_with_node(staking_info_with_node):
    """Round-trip byte serialization with a node target."""
    data = staking_info_with_node.to_bytes()
    restored = StakingInfo.from_bytes(data)

    assert restored.decline_reward == staking_info_with_node.decline_reward
    assert restored.stake_period_start == staking_info_with_node.stake_period_start
    assert restored.pending_reward == staking_info_with_node.pending_reward
    assert restored.staked_to_me == staking_info_with_node.staked_to_me
    assert restored.staked_account_id is None
    assert restored.staked_node_id == staking_info_with_node.staked_node_id


def test_str_output_format(staking_info_with_account):
    """Check human-readable string formatting."""
    expected = (
        "StakingInfo(\n"
        "  decline_reward=True,\n"
        "  stake_period_start=100.000000200,\n"
        "  pending_reward=0.00001234 \u210f,\n"
        "  staked_to_me=0.00005678 \u210f,\n"
        "  staked_account_id=0.0.123,\n"
        "  staked_node_id=None\n"
        ")"
    )

    assert str(staking_info_with_account) == expected


def test_repr_contains_class_name_and_fields(staking_info_with_node):
    """Ensure repr includes key fields for debugging."""
    rep = repr(staking_info_with_node)

    assert "StakingInfo(" in rep
    assert "decline_reward=False" in rep
    assert "stake_period_start=" in rep
    assert "pending_reward=Hbar(0.00002222)" in rep
    assert "staked_to_me=Hbar(0.00004444)" in rep
    assert "staked_node_id=3" in rep


def test_proto_round_trip_default():
    """Round-trip proto serialization for default values."""
    default_info = StakingInfo()
    restored = StakingInfo._from_proto(default_info._to_proto())

    assert restored.decline_reward is False  # proto3 scalar default
    assert restored.stake_period_start is None
    assert restored.pending_reward == Hbar.from_tinybars(0)  # proto3 scalar default
    assert restored.staked_to_me == Hbar.from_tinybars(0)  # proto3 scalar default
    assert restored.staked_account_id is None
    assert restored.staked_node_id is None
