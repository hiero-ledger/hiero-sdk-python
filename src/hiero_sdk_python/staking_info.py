"""
StakingInfo class.
"""

from dataclasses import dataclass
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.basic_types_pb2 import StakingInfo as StakingInfoProto
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp


@dataclass(frozen=True)
class StakingInfo:
    """
    Represents staking-related information for an account.

    Attributes:
        decline_reward (Optional[bool]): Whether rewards are declined.
        stake_period_start (Optional[Timestamp]): Start of the staking period.
        pending_reward (Optional[Hbar]): Pending staking reward in Hbar.
        staked_to_me (Optional[Hbar]): Amount staked to this account in Hbar.
        staked_account_id (Optional[AccountId]): Account ID this account is staked to.
        staked_node_id (Optional[int]): Node ID this account is staked to.
    """

    decline_reward: Optional[bool] = None
    stake_period_start: Optional[Timestamp] = None
    pending_reward: Optional[Hbar] = None
    staked_to_me: Optional[Hbar] = None
    staked_account_id: Optional[AccountId] = None
    staked_node_id: Optional[int] = None

    def __post_init__(self) -> None:
        if self.staked_account_id is not None and self.staked_node_id is not None:
            raise ValueError("Only one of staked_account_id or staked_node_id can be set.")

    @classmethod
    def _from_proto(cls, proto: StakingInfoProto) -> "StakingInfo":
        """
        Creates a StakingInfo instance from its protobuf representation.
        """
        if proto is None:
            raise ValueError("Staking info proto is None")

        decline_reward = proto.decline_reward
        
        stake_period_start = None
        if proto.HasField("stake_period_start"):
            stake_period_start = Timestamp._from_protobuf(proto.stake_period_start)

        pending_reward=Hbar.from_tinybars(proto.pending_reward)
        staked_to_me=Hbar.from_tinybars(proto.staked_to_me)

        staked_account_id = None
        if proto.HasField("staked_account_id"):
            staked_account_id = AccountId._from_proto(proto.staked_account_id)

        staked_node_id = None
        if proto.HasField("staked_node_id"):
            staked_node_id = proto.staked_node_id

        return cls(
            decline_reward=proto.decline_reward,
            stake_period_start=stake_period_start,
            pending_reward=pending_reward,
            staked_to_me=staked_to_me,
            staked_account_id=staked_account_id,
            staked_node_id=staked_node_id,
        )

    def _to_proto(self) -> StakingInfoProto:
        """
        Converts this StakingInfo instance to its protobuf representation.
        """
        proto = StakingInfoProto()

        if self.decline_reward is not None:
            proto.decline_reward = bool(self.decline_reward)
        if self.stake_period_start is not None:
            proto.stake_period_start.CopyFrom(self.stake_period_start._to_protobuf())
        if self.pending_reward is not None:
            proto.pending_reward = self.pending_reward.to_tinybars()
        if self.staked_to_me is not None:
            proto.staked_to_me = self.staked_to_me.to_tinybars()
        if self.staked_account_id is not None:
            proto.staked_account_id.CopyFrom(self.staked_account_id._to_proto())
        if self.staked_node_id is not None:
            proto.staked_node_id = self.staked_node_id

        return proto

    @classmethod
    def from_bytes(cls, data: bytes) -> "StakingInfo":
        """
        Creates a StakingInfo instance from protobuf-encoded bytes.
        """
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if len(data) == 0:
            raise ValueError("data cannot be empty")

        try:
            proto = StakingInfoProto.FromString(data)
        except Exception as exc:
            raise ValueError(f"Failed to parse StakingInfo bytes: {exc}") from exc

        return cls._from_proto(proto)

    def to_bytes(self) -> bytes:
        """
        Serializes this StakingInfo instance to protobuf-encoded bytes.
        """
        return self._to_proto().SerializeToString()

    def __str__(self) -> str:
        return (
            "StakingInfo(\n"
            f"  decline_reward={self.decline_reward},\n"
            f"  stake_period_start={self.stake_period_start},\n"
            f"  pending_reward={self.pending_reward},\n"
            f"  staked_to_me={self.staked_to_me},\n"
            f"  staked_account_id={self.staked_account_id},\n"
            f"  staked_node_id={self.staked_node_id}\n"
            ")"
        )

    def __repr__(self) -> str:
        return (
            "StakingInfo("
            f"decline_reward={self.decline_reward!r}, "
            f"stake_period_start={self.stake_period_start!r}, "
            f"pending_reward={self.pending_reward!r}, "
            f"staked_to_me={self.staked_to_me!r}, "
            f"staked_account_id={self.staked_account_id!r}, "
            f"staked_node_id={self.staked_node_id!r}"
            ")"
        )
