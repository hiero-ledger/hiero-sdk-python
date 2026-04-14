# pylint: disable=too-many-instance-attributes
"""AccountInfo class."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.crypto_get_info_pb2 import CryptoGetInfoResponse
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.staking_info import StakingInfo
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_relationship import TokenRelationship


@dataclass
class AccountInfo:
    """
    Contains information about an account.

    Attributes:
        account_id (AccountId, optional): The ID of this account.
        contract_account_id (str, optional): The contract account ID.
        is_deleted (bool, optional): Whether the account has been deleted.
        proxy_received (Hbar, optional): The total number of tinybars proxy staked to this account.
        key (Key, optional): The key for this account.
        balance (Hbar, optional): The current balance of account in hbar.
        receiver_signature_required (Optional[bool]): If true, this account's key must sign
            any transaction depositing into this account.
        expiration_time (Timestamp, optional): The timestamp at which this account
            is set to expire.
        auto_renew_period (Duration, optional): The duration for which this account
            will automatically renew.
        token_relationships (list[TokenRelationship], optional): List of token relationships
            associated with this account.
        account_memo (str, optional): The memo associated with this account.
        owned_nfts (int, optional): The number of NFTs owned by this account.
        staking_info (StakingInfo, optional): The staking information for this account.
    """

    account_id: AccountId | None = None
    contract_account_id: str | None = None
    is_deleted: bool | None = None
    proxy_received: Hbar | None = None
    key: Key | None = None
    balance: Hbar | None = None
    receiver_signature_required: bool | None = None
    expiration_time: Timestamp | None = None
    auto_renew_period: Duration | None = None
    token_relationships: list[TokenRelationship] = field(default_factory=list)
    account_memo: str | None = None
    owned_nfts: int | None = None
    max_automatic_token_associations: int | None = None
    staking_info: StakingInfo | None = None

    @classmethod
    def _from_proto(cls, proto: CryptoGetInfoResponse.AccountInfo) -> AccountInfo:
        """Creates an AccountInfo instance from its protobuf representation.
        Deserializes a `CryptoGetInfoResponse.AccountInfo` message into this
        SDK's `AccountInfo` object. This method handles the conversion of
        protobuf types to their corresponding SDK types (e.g., tinybars to
        `Hbar`, proto `Timestamp` to SDK `Timestamp`).

        Args:
            proto (CryptoGetInfoResponse.AccountInfo): The source protobuf
                message containing account information.

        Returns:
            AccountInfo: A new `AccountInfo` instance populated with data
                from the protobuf message.

        Raises:
            ValueError: If the input `proto` is None.
        """
        if proto is None:
            raise ValueError("Account info proto is None")

        account_info: AccountInfo = cls(
            account_id=AccountId._from_proto(proto.accountID) if proto.accountID else None,
            contract_account_id=proto.contractAccountID,
            is_deleted=proto.deleted,
            proxy_received=Hbar.from_tinybars(proto.proxyReceived),
            key=Key.from_proto_key(proto.key) if proto.key else None,
            balance=Hbar.from_tinybars(proto.balance),
            receiver_signature_required=proto.receiverSigRequired,
            expiration_time=(Timestamp._from_protobuf(proto.expirationTime) if proto.expirationTime else None),
            auto_renew_period=(Duration._from_proto(proto.autoRenewPeriod) if proto.autoRenewPeriod else None),
            token_relationships=[
                TokenRelationship._from_proto(relationship) for relationship in proto.tokenRelationships
            ],
            account_memo=proto.memo,
            owned_nfts=proto.ownedNfts,
            max_automatic_token_associations=proto.max_automatic_token_associations,
            staking_info=(StakingInfo._from_proto(proto.staking_info) if proto.HasField("staking_info") else None),
        )

        return account_info

    def _to_proto(self) -> CryptoGetInfoResponse.AccountInfo:
        """Converts this AccountInfo object to its protobuf representation.
        Serializes this `AccountInfo` instance into a
        `CryptoGetInfoResponse.AccountInfo` message. This method handles
        the conversion of SDK types back to their protobuf equivalents
        (e.g., `Hbar` to tinybars, SDK `Timestamp` to proto `Timestamp`).

        Note:
            SDK fields that are `None` will be serialized as their
            default protobuf values (e.g., 0 for integers, False for booleans,
            empty strings/bytes).

        Returns:
            CryptoGetInfoResponse.AccountInfo: The protobuf message
                representation of this `AccountInfo` object.
        """
        proto = CryptoGetInfoResponse.AccountInfo(
            accountID=self.account_id._to_proto() if self.account_id else None,
            contractAccountID=self.contract_account_id,
            deleted=self.is_deleted,
            proxyReceived=self.proxy_received.to_tinybars() if self.proxy_received else None,
            key=self.key._to_proto() if self.key else None,
            balance=self.balance.to_tinybars() if self.balance else None,
            receiverSigRequired=self.receiver_signature_required,
            expirationTime=self.expiration_time._to_protobuf() if self.expiration_time else None,
            autoRenewPeriod=self.auto_renew_period._to_proto() if self.auto_renew_period else None,
            tokenRelationships=[relationship._to_proto() for relationship in self.token_relationships],
            memo=self.account_memo,
            ownedNfts=self.owned_nfts,
            max_automatic_token_associations=self.max_automatic_token_associations,
        )
        if self.staking_info is not None:
            proto.staking_info.CopyFrom(self.staking_info._to_proto())
        return proto

    def __str__(self) -> str:
        """Returns a user-friendly string representation of the AccountInfo."""
        # Define simple fields to print if they exist
        # Format: (value_to_check, label)
        simple_fields = [
            (self.account_id, "Account ID"),
            (self.contract_account_id, "Contract Account ID"),
            (self.balance, "Balance"),
            (self.key, "Key"),
            (self.account_memo, "Memo"),
            (self.owned_nfts, "Owned NFTs"),
            (self.max_automatic_token_associations, "Max Automatic Token Associations"),
            (self.staking_info, "Staking Info"),
            (self.proxy_received, "Proxy Received"),
            (self.expiration_time, "Expiration Time"),
            (self.auto_renew_period, "Auto Renew Period"),
        ]

        # Use a list comprehension to process simple fields (reduces complexity score)
        lines = [f"{label}: {val}" for val, label in simple_fields if val is not None]

        # 2. Handle booleans and special cases explicitly
        if self.is_deleted is not None:
            lines.append(f"Deleted: {self.is_deleted}")

        if self.receiver_signature_required is not None:
            lines.append(f"Receiver Signature Required: {self.receiver_signature_required}")

        if self.token_relationships:
            lines.append(f"Token Relationships: {len(self.token_relationships)}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Returns a string representation of the AccountInfo object for debugging."""
        parts = [
            f"account_id={self.account_id!r}",
            f"contract_account_id={self.contract_account_id!r}",
            f"is_deleted={self.is_deleted!r}",
            f"balance={self.balance!r}",
            f"receiver_signature_required={self.receiver_signature_required!r}",
            f"owned_nfts={self.owned_nfts!r}",
            f"account_memo={self.account_memo!r}",
        ]
        if self.staking_info is not None:
            parts.append(f"staking_info={self.staking_info!r}")
        return f"AccountInfo({', '.join(parts)})"

    @property
    def staked_account_id(self):
        """Deprecated: use staking_info.staked_account_id instead."""
        warnings.warn(
            "AccountInfo.staked_account_id is deprecated, use AccountInfo.staking_info.staked_account_id instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.staking_info.staked_account_id if self.staking_info else None

    @staked_account_id.setter
    def staked_account_id(self, value):
        """Deprecated setter: use staking_info.staked_account_id instead."""
        warnings.warn(
            "AccountInfo.staked_account_id setter is deprecated, use AccountInfo.staking_info instead",
            DeprecationWarning,
            stacklevel=2,
        )
        if self.staking_info is None:
            object.__setattr__(self, "staking_info", StakingInfo(staked_account_id=value))
        else:
            # Reconstruct StakingInfo with updated field, clearing staked_node_id oneof conflict
            object.__setattr__(
                self,
                "staking_info",
                StakingInfo(
                    pending_reward=self.staking_info.pending_reward,
                    staked_to_me=self.staking_info.staked_to_me,
                    stake_period_start=self.staking_info.stake_period_start,
                    staked_account_id=value,
                    staked_node_id=None,  # Clear oneof conflict
                    decline_reward=self.staking_info.decline_reward,
                ),
            )

    @property
    def staked_node_id(self):
        """Deprecated: use staking_info.staked_node_id instead."""
        warnings.warn(
            "AccountInfo.staked_node_id is deprecated, use AccountInfo.staking_info.staked_node_id instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.staking_info.staked_node_id if self.staking_info else None

    @staked_node_id.setter
    def staked_node_id(self, value):
        """Deprecated setter: use staking_info.staked_node_id instead."""
        warnings.warn(
            "AccountInfo.staked_node_id setter is deprecated, use AccountInfo.staking_info instead",
            DeprecationWarning,
            stacklevel=2,
        )
        if self.staking_info is None:
            object.__setattr__(self, "staking_info", StakingInfo(staked_node_id=value))
        else:
            # Reconstruct StakingInfo with updated field, clearing staked_account_id oneof conflict
            object.__setattr__(
                self,
                "staking_info",
                StakingInfo(
                    pending_reward=self.staking_info.pending_reward,
                    staked_to_me=self.staking_info.staked_to_me,
                    stake_period_start=self.staking_info.stake_period_start,
                    staked_account_id=None,  # Clear oneof conflict
                    staked_node_id=value,
                    decline_reward=self.staking_info.decline_reward,
                ),
            )

    @property
    def decline_staking_reward(self):
        """Deprecated: use staking_info.decline_reward instead."""
        warnings.warn(
            "AccountInfo.decline_staking_reward is deprecated, use AccountInfo.staking_info.decline_reward instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.staking_info.decline_reward if self.staking_info else None

    @decline_staking_reward.setter
    def decline_staking_reward(self, value):
        """Deprecated setter: use staking_info.decline_reward instead."""
        warnings.warn(
            "AccountInfo.decline_staking_reward setter is deprecated, use AccountInfo.staking_info instead",
            DeprecationWarning,
            stacklevel=2,
        )
        if self.staking_info is None:
            object.__setattr__(self, "staking_info", StakingInfo(decline_reward=value))
        else:
            # Reconstruct StakingInfo with updated field
            object.__setattr__(
                self,
                "staking_info",
                StakingInfo(
                    pending_reward=self.staking_info.pending_reward,
                    staked_to_me=self.staking_info.staked_to_me,
                    stake_period_start=self.staking_info.stake_period_start,
                    staked_account_id=self.staking_info.staked_account_id,
                    staked_node_id=self.staking_info.staked_node_id,
                    decline_reward=value,
                ),
            )


# ---------------------------------------------------------------------------
# Backwards-compatible constructor: accept legacy staking kwargs
# ---------------------------------------------------------------------------
_ACCOUNT_INFO_INIT_SENTINEL = object()
_orig_account_info_init = AccountInfo.__init__


def _wrapped_account_info_init(
    self,
    *args,
    staked_account_id=_ACCOUNT_INFO_INIT_SENTINEL,
    staked_node_id=_ACCOUNT_INFO_INIT_SENTINEL,
    decline_staking_reward=_ACCOUNT_INFO_INIT_SENTINEL,
    **kwargs,
):
    _orig_account_info_init(self, *args, **kwargs)
    _legacy = [
        k
        for k, v in [
            ("staked_account_id", staked_account_id),
            ("staked_node_id", staked_node_id),
            ("decline_staking_reward", decline_staking_reward),
        ]
        if v is not _ACCOUNT_INFO_INIT_SENTINEL
    ]
    if _legacy:
        warnings.warn(
            f"Passing {', '.join(_legacy)} to AccountInfo() is deprecated; use staking_info=StakingInfo(...) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            if staked_account_id is not _ACCOUNT_INFO_INIT_SENTINEL:
                self.staked_account_id = staked_account_id
            if staked_node_id is not _ACCOUNT_INFO_INIT_SENTINEL:
                self.staked_node_id = staked_node_id
            if decline_staking_reward is not _ACCOUNT_INFO_INIT_SENTINEL:
                self.decline_staking_reward = decline_staking_reward


AccountInfo.__init__ = _wrapped_account_info_init
