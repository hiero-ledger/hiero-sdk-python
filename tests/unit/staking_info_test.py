"""Tests for the StakingInfo class."""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.basic_types_pb2 import StakingInfo as StakingInfoProto
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.staking_info import StakingInfo
from hiero_sdk_python.timestamp import Timestamp

pytestmark = pytest.mark.unit


@pytest.fixture(name="staking_info_with_account")
def fixture_staking_info_with_account():
    return StakingInfo(
        decline_reward=True,
        stake_period_start=Timestamp(100, 200),
        pending_reward=Hbar.from_tinybars(1234),
        staked_to_me=Hbar.from_tinybars(5678),
        staked_account_id=AccountId(0, 0, 123),
    )


@pytest.fixture(name="staking_info_with_node")
def fixture_staking_info_with_node():
    return StakingInfo(
        decline_reward=False,
        stake_period_start=Timestamp(300, 400),
        pending_reward=Hbar.from_tinybars(2222),
        staked_to_me=Hbar.from_tinybars(4444),
        staked_node_id=3,
    )


@pytest.fixture(name="proto_staking_info_with_account")
def fixture_proto_staking_info_with_account():
    return StakingInfoProto(
        decline_reward=True,
        stake_period_start=Timestamp(100, 200)._to_protobuf(),
        pending_reward=1234,
        staked_to_me=5678,
        staked_account_id=AccountId(0, 0, 123)._to_proto(),
    )


@pytest.fixture(name="proto_staking_info_with_node")
def fixture_proto_staking_info_with_node():
    return StakingInfoProto(
        decline_reward=False,
        stake_period_start=Timestamp(300, 400)._to_protobuf(),
        pending_reward=2222,
        staked_to_me=4444,
        staked_node_id=3,
    )


def test_default_initialization():
    staking_info = StakingInfo()

    assert staking_info.decline_reward is None
    assert staking_info.stake_period_start is None
    assert staking_info.pending_reward is None
    assert staking_info.staked_to_me is None
    assert staking_info.staked_account_id is None
    assert staking_info.staked_node_id is None


def test_initialization_with_account(staking_info_with_account):
    staking_info = staking_info_with_account

    assert staking_info.decline_reward is True
    assert staking_info.stake_period_start == Timestamp(100, 200)
    assert staking_info.pending_reward == Hbar.from_tinybars(1234)
    assert staking_info.staked_to_me == Hbar.from_tinybars(5678)
    assert str(staking_info.staked_account_id) == "0.0.123"
    assert staking_info.staked_node_id is None


def test_initialization_with_node(staking_info_with_node):
    staking_info = staking_info_with_node

    assert staking_info.decline_reward is False
    assert staking_info.stake_period_start == Timestamp(300, 400)
    assert staking_info.pending_reward == Hbar.from_tinybars(2222)
    assert staking_info.staked_to_me == Hbar.from_tinybars(4444)
    assert staking_info.staked_account_id is None
    assert staking_info.staked_node_id == 3


def test_oneof_validation_raises():
    with pytest.raises(
        ValueError, match=r"Only one of staked_account_id or staked_node_id can be set\."
    ):
        StakingInfo(
            staked_account_id=AccountId(0, 0, 123),
            staked_node_id=3,
        )


def test_from_proto_with_account(proto_staking_info_with_account):
    staking_info = StakingInfo.from_proto(proto_staking_info_with_account)

    assert staking_info.decline_reward is True
    assert staking_info.stake_period_start == Timestamp(100, 200)
    assert staking_info.pending_reward == Hbar.from_tinybars(1234)
    assert staking_info.staked_to_me == Hbar.from_tinybars(5678)
    assert str(staking_info.staked_account_id) == "0.0.123"
    assert staking_info.staked_node_id is None


def test_from_proto_with_node(proto_staking_info_with_node):
    staking_info = StakingInfo.from_proto(proto_staking_info_with_node)

    assert staking_info.decline_reward is False
    assert staking_info.stake_period_start == Timestamp(300, 400)
    assert staking_info.pending_reward == Hbar.from_tinybars(2222)
    assert staking_info.staked_to_me == Hbar.from_tinybars(4444)
    assert staking_info.staked_account_id is None
    assert staking_info.staked_node_id == 3


def test_from_proto_none_raises():
    with pytest.raises(ValueError, match=r"Staking info proto is None"):
        StakingInfo.from_proto(None)


def test_to_proto_with_account(staking_info_with_account):
    proto = staking_info_with_account.to_proto()

    assert proto.decline_reward is True
    assert proto.HasField("stake_period_start")
    assert proto.stake_period_start == Timestamp(100, 200)._to_protobuf()
    assert proto.pending_reward == 1234
    assert proto.staked_to_me == 5678
    assert proto.HasField("staked_account_id")
    assert proto.staked_account_id == AccountId(0, 0, 123)._to_proto()
    assert not proto.HasField("staked_node_id")


def test_to_proto_with_node(staking_info_with_node):
    proto = staking_info_with_node.to_proto()

    assert proto.decline_reward is False
    assert proto.HasField("stake_period_start")
    assert proto.stake_period_start == Timestamp(300, 400)._to_protobuf()
    assert proto.pending_reward == 2222
    assert proto.staked_to_me == 4444
    assert not proto.HasField("staked_account_id")
    assert proto.HasField("staked_node_id")
    assert proto.staked_node_id == 3


def test_proto_round_trip_with_account(staking_info_with_account):
    restored = StakingInfo.from_proto(staking_info_with_account.to_proto())

    assert restored.decline_reward == staking_info_with_account.decline_reward
    assert restored.stake_period_start == staking_info_with_account.stake_period_start
    assert restored.pending_reward == staking_info_with_account.pending_reward
    assert restored.staked_to_me == staking_info_with_account.staked_to_me
    assert str(restored.staked_account_id) == str(staking_info_with_account.staked_account_id)
    assert restored.staked_node_id is None


def test_proto_round_trip_with_node(staking_info_with_node):
    restored = StakingInfo.from_proto(staking_info_with_node.to_proto())

    assert restored.decline_reward == staking_info_with_node.decline_reward
    assert restored.stake_period_start == staking_info_with_node.stake_period_start
    assert restored.pending_reward == staking_info_with_node.pending_reward
    assert restored.staked_to_me == staking_info_with_node.staked_to_me
    assert restored.staked_account_id is None
    assert restored.staked_node_id == staking_info_with_node.staked_node_id


def test_from_bytes_deserializes(staking_info_with_account):
    data = staking_info_with_account.to_bytes()
    restored = StakingInfo.from_bytes(data)

    assert restored.decline_reward == staking_info_with_account.decline_reward
    assert restored.stake_period_start == staking_info_with_account.stake_period_start
    assert restored.pending_reward == staking_info_with_account.pending_reward
    assert restored.staked_to_me == staking_info_with_account.staked_to_me
    assert str(restored.staked_account_id) == str(staking_info_with_account.staked_account_id)
    assert restored.staked_node_id is None


def test_from_bytes_empty_raises():
    with pytest.raises(ValueError, match=r"data cannot be empty"):
        StakingInfo.from_bytes(b"")


def test_to_bytes_produces_non_empty_bytes(staking_info_with_node):
    data = staking_info_with_node.to_bytes()

    assert isinstance(data, bytes)
    assert len(data) > 0


def test_bytes_round_trip_with_node(staking_info_with_node):
    data = staking_info_with_node.to_bytes()
    restored = StakingInfo.from_bytes(data)

    assert restored.decline_reward == staking_info_with_node.decline_reward
    assert restored.stake_period_start == staking_info_with_node.stake_period_start
    assert restored.pending_reward == staking_info_with_node.pending_reward
    assert restored.staked_to_me == staking_info_with_node.staked_to_me
    assert restored.staked_account_id is None
    assert restored.staked_node_id == staking_info_with_node.staked_node_id


def test_str_output_format(staking_info_with_account):
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
    rep = repr(staking_info_with_node)

    assert "StakingInfo(" in rep
    assert "decline_reward=False" in rep
    assert "stake_period_start=" in rep
    assert "pending_reward=Hbar(0.00002222)" in rep
    assert "staked_to_me=Hbar(0.00004444)" in rep
    assert "staked_node_id=3" in rep
