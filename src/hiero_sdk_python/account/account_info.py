# pylint: disable=too-many-instance-attributes
"""
AccountInfo class.
"""

from dataclasses import dataclass, field
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.basic_types_pb2 import StakingInfo
from hiero_sdk_python.hapi.services.crypto_get_info_pb2 import CryptoGetInfoResponse
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_relationship import TokenRelationship


@dataclass
class AccountInfo:
    """
    Contains information about an account.

    Attributes:
        account_id (Optional[AccountId]): The ID of this account.
        contract_account_id (Optional[str]): The contract account ID.
        is_deleted (Optional[bool]): Whether the account has been deleted.
        proxy_received (Optional[Hbar]): The total number of tinybars proxy staked to this account.
        key (Optional[PublicKey]): The key for this account.
        balance (Optional[Hbar]): The current balance of account in hbar.
        receiver_signature_required (Optional[bool]): If true, this account's key must sign
            any transaction depositing into this account.
        expiration_time (Optional[Timestamp]): The timestamp at which this account
            is set to expire.
        auto_renew_period (Optional[Duration]): The duration for which this account
            will automatically renew.
        token_relationships (list[TokenRelationship]): List of token relationships
            associated with this account.
        account_memo (Optional[str]): The memo associated with this account.
        owned_nfts (Optional[int]): The number of NFTs owned by this account.
        staked_account_id (Optional[AccountId]): The account to which this account is staked.
        staked_node_id (Optional[int]): The node to which this account is staked.
        decline_staking_reward (bool): Whether this account declines receiving staking rewards. 
    """

    account_id: Optional[AccountId] = None
    contract_account_id: Optional[str] = None
    is_deleted: Optional[bool] = None
    proxy_received: Optional[Hbar] = None
    key: Optional[PublicKey] = None
    balance: Optional[Hbar] = None
    receiver_signature_required: Optional[bool] = None
    expiration_time: Optional[Timestamp] = None
    auto_renew_period: Optional[Duration] = None
    token_relationships: list[TokenRelationship] = field(default_factory=list)
    account_memo: Optional[str] = None
    owned_nfts: Optional[int] = None
    max_automatic_token_associations: Optional[int] = None
    staked_account_id: Optional[AccountId] = None
    staked_node_id: Optional[int] = None
    decline_staking_reward: Optional[bool] = None

    @classmethod
    def _from_proto(cls, proto: CryptoGetInfoResponse.AccountInfo) -> "AccountInfo":
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

        account_info: "AccountInfo" = cls(
            account_id=AccountId._from_proto(proto.accountID) if proto.accountID else None,
            contract_account_id=proto.contractAccountID,
            is_deleted=proto.deleted,
            proxy_received=Hbar.from_tinybars(proto.proxyReceived),
            key=PublicKey._from_proto(proto.key) if proto.key else None,
            balance=Hbar.from_tinybars(proto.balance),
            receiver_signature_required=proto.receiverSigRequired,
            expiration_time=(
                Timestamp._from_protobuf(proto.expirationTime) if proto.expirationTime else None
            ),
            auto_renew_period=(
                Duration._from_proto(proto.autoRenewPeriod) if proto.autoRenewPeriod else None
            ),
            token_relationships=[
                TokenRelationship._from_proto(relationship)
                for relationship in proto.tokenRelationships
            ],
            account_memo=proto.memo,
            owned_nfts=proto.ownedNfts,
            max_automatic_token_associations=proto.max_automatic_token_associations,
        )

        staking_info = proto.staking_info if proto.HasField('staking_info') else None

        if staking_info:
            account_info.staked_account_id = (
                AccountId._from_proto(staking_info.staked_account_id) 
                if staking_info.HasField('staked_account_id') else None
            )
            account_info.staked_node_id = (
                staking_info.staked_node_id 
                if staking_info.HasField('staked_node_id') else None
            )
            account_info.decline_staking_reward = staking_info.decline_reward

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
        return CryptoGetInfoResponse.AccountInfo(
            accountID=self.account_id._to_proto() if self.account_id else None,
            contractAccountID=self.contract_account_id,
            deleted=self.is_deleted,
            proxyReceived=self.proxy_received.to_tinybars() if self.proxy_received else None,
            key=self.key._to_proto() if self.key else None,
            balance=self.balance.to_tinybars() if self.balance else None,
            receiverSigRequired=self.receiver_signature_required,
            expirationTime=self.expiration_time._to_protobuf() if self.expiration_time else None,
            autoRenewPeriod=self.auto_renew_period._to_proto() if self.auto_renew_period else None,
            tokenRelationships=[
                relationship._to_proto() for relationship in self.token_relationships
            ],
            memo=self.account_memo,
            ownedNfts=self.owned_nfts,
            max_automatic_token_associations=self.max_automatic_token_associations,
            staking_info=StakingInfo(
                staked_account_id=self.staked_account_id._to_proto() if self.staked_account_id else None,
                staked_node_id=self.staked_node_id if self.staked_node_id else None,
                decline_reward=self.decline_staking_reward
            ),
        )
