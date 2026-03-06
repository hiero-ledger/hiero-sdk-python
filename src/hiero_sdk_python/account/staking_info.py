"""
StakingInfo wrapper class for AccountInfo.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.basic_types_pb2 import StakingInfo as StakingInfoProto
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp as TimestampProto
from hiero_sdk_python.hbar import Hbar


@dataclass
class StakingInfo:
    """
    Represents staking-related information for an account.

    Attributes:
        pending_reward (Optional[Hbar]): Pending staking reward in Hbar.
        staked_to_me (Optional[Hbar]): Amount staked to this account in Hbar.
        stake_period_start (Optional[datetime]): Start of the staking period.
        staked_account_id (Optional[AccountId]): Account ID this account is staked to.
        staked_node_id (Optional[int]): Node ID this account is staked to.
        decline_staking_reward (Optional[bool]): Whether staking rewards are declined.
    """

    pending_reward: Optional[Hbar] = None
    staked_to_me: Optional[Hbar] = None
    stake_period_start: Optional[datetime] = None
    staked_account_id: Optional[AccountId] = None
    staked_node_id: Optional[int] = None
    decline_staking_reward: Optional[bool] = None

    @classmethod
    def _from_proto(cls, proto: StakingInfoProto) -> "StakingInfo":
        """Creates a StakingInfo instance from its protobuf representation.

        Args:
            proto (StakingInfoProto): The source protobuf StakingInfo message.

        Returns:
            StakingInfo: A new StakingInfo instance populated from the protobuf message.

        Raises:
            ValueError: If the input proto is None.
        """
        if proto is None:
            raise ValueError("Staking info proto is None")

        pending_reward = Hbar.from_tinybars(proto.pending_reward)
        staked_to_me = Hbar.from_tinybars(proto.staked_to_me)

        stake_period_start = None
        if proto.HasField("stake_period_start"):
            stake_period_start = datetime.fromtimestamp(
                proto.stake_period_start.seconds, tz=timezone.utc
            )

        staked_account_id = None
        if proto.HasField("staked_account_id"):
            staked_account_id = AccountId._from_proto(proto.staked_account_id)

        staked_node_id = None
        if proto.HasField("staked_node_id"):
            staked_node_id = proto.staked_node_id

        return cls(
            pending_reward=pending_reward,
            staked_to_me=staked_to_me,
            stake_period_start=stake_period_start,
            staked_account_id=staked_account_id,
            staked_node_id=staked_node_id,
            decline_staking_reward=proto.decline_reward,
        )

    def _to_proto(self) -> StakingInfoProto:
        """Converts this StakingInfo instance to its protobuf representation.

        Returns:
            StakingInfoProto: The protobuf StakingInfo message.
        """
        proto = StakingInfoProto()

        if self.decline_staking_reward is not None:
            proto.decline_reward = bool(self.decline_staking_reward)
        if self.stake_period_start is not None:
            proto.stake_period_start.CopyFrom(
                TimestampProto(
                    seconds=int(self.stake_period_start.timestamp()),
                    nanos=0,
                )
            )
        if self.pending_reward is not None:
            proto.pending_reward = self.pending_reward.to_tinybars()
        if self.staked_to_me is not None:
            proto.staked_to_me = self.staked_to_me.to_tinybars()
        if self.staked_account_id is not None:
            proto.staked_account_id.CopyFrom(self.staked_account_id._to_proto())
        if self.staked_node_id is not None:
            proto.staked_node_id = self.staked_node_id

        return proto

    def __str__(self) -> str:
        """Returns a user-friendly string representation of the StakingInfo."""
        lines = []
        if self.pending_reward is not None:
            lines.append(f"  Pending Reward: {self.pending_reward}")
        if self.staked_to_me is not None:
            lines.append(f"  Staked To Me: {self.staked_to_me}")
        if self.stake_period_start is not None:
            lines.append(f"  Stake Period Start: {self.stake_period_start}")
        if self.staked_account_id is not None:
            lines.append(f"  Staked Account ID: {self.staked_account_id}")
        if self.staked_node_id is not None:
            lines.append(f"  Staked Node ID: {self.staked_node_id}")
        if self.decline_staking_reward is not None:
            lines.append(f"  Decline Staking Reward: {self.decline_staking_reward}")
        return "StakingInfo(\n" + "\n".join(lines) + "\n)"

    def __repr__(self) -> str:
        """Returns a string representation of the StakingInfo object for debugging."""
        return (
            "StakingInfo("
            f"pending_reward={self.pending_reward!r}, "
            f"staked_to_me={self.staked_to_me!r}, "
            f"stake_period_start={self.stake_period_start!r}, "
            f"staked_account_id={self.staked_account_id!r}, "
            f"staked_node_id={self.staked_node_id!r}, "
            f"decline_staking_reward={self.decline_staking_reward!r}"
            ")"
        )
