# pylint: disable=too-many-instance-attributes
"""
This module contains the ContractInfo class, which is used to store information about a contract.
"""

import datetime
from dataclasses import dataclass, field
from typing import Callable, Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.contract_get_info_pb2 import ContractGetInfoResponse
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_relationship import TokenRelationship


@dataclass
class ContractInfo:
    """
    Information about a contract stored on the network.

    Attributes:
        contract_id (Optional[ContractId]): The ID of the contract
        account_id (Optional[AccountId]): The ID of the account owned by the contract
        contract_account_id (Optional[str]): The contract's EVM address (hex).
        admin_key (Optional[PublicKey]): The key that can modify this contract
        expiration_time (Optional[Timestamp]): When the contract will expire
        auto_renew_period (Optional[Duration]): The period for which the contract will auto-renew
        auto_renew_account_id (Optional[AccountId]):
            The ID of the account that will auto-renew the contract
        storage (Optional[int]): The storage used by the contract
        contract_memo (Optional[str]): The memo associated with the contract
        balance (Optional[int]): The balance of the contract
        is_deleted (Optional[bool]): Whether the contract has been deleted
        ledger_id (Optional[bytes]): The ID of the ledger this contract exists in
        max_automatic_token_associations (Optional[int]):
            The maximum number of token associations that can be automatically renewed
        token_relationships (list[TokenRelationship]): The token relationships of the contract
    """

    contract_id: Optional[ContractId] = None
    account_id: Optional[AccountId] = None
    contract_account_id: Optional[str] = None
    admin_key: Optional[PublicKey] = None
    expiration_time: Optional[Timestamp] = None
    auto_renew_period: Optional[Duration] = None
    auto_renew_account_id: Optional[AccountId] = None
    storage: Optional[int] = None
    contract_memo: Optional[str] = None
    balance: Optional[int] = None
    is_deleted: Optional[bool] = None
    ledger_id: Optional[bytes] = None
    max_automatic_token_associations: Optional[int] = None
    token_relationships: list[TokenRelationship] = field(default_factory=list)

    @classmethod
    def _from_proto(cls, proto: ContractGetInfoResponse.ContractInfo) -> "ContractInfo":
        """
        Creates a ContractInfo instance from its protobuf representation.

        Args:
            proto (ContractGetInfoResponse.ContractInfo): The protobuf to convert from.

        Returns:
            ContractInfo: A new ContractInfo instance.
        """
        if proto is None:
            raise ValueError("Contract info proto is None")

        return cls(
            contract_id=(
                cls._from_proto_field(proto, "contractID", ContractId._from_proto)
            ),
            account_id=(
                cls._from_proto_field(proto, "accountID", AccountId._from_proto)
            ),
            contract_account_id=proto.contractAccountID,
            admin_key=(cls._from_proto_field(proto, "adminKey", PublicKey._from_proto)),
            expiration_time=(
                cls._from_proto_field(proto, "expirationTime", Timestamp._from_protobuf)
            ),
            auto_renew_period=(
                cls._from_proto_field(proto, "autoRenewPeriod", Duration._from_proto)
            ),
            auto_renew_account_id=(
                cls._from_proto_field(
                    proto, "auto_renew_account_id", AccountId._from_proto
                )
            ),
            storage=proto.storage,
            contract_memo=proto.memo,
            balance=proto.balance,
            is_deleted=proto.deleted,
            ledger_id=proto.ledger_id,
            max_automatic_token_associations=proto.max_automatic_token_associations,
            token_relationships=[
                TokenRelationship._from_proto(relationship)
                for relationship in proto.tokenRelationships
            ],
        )

    def _to_proto(self) -> ContractGetInfoResponse.ContractInfo:
        """
        Converts this ContractInfo instance to its protobuf representation.

        Returns:
            ContractGetInfoResponse.ContractInfo: The protobuf representation of this ContractInfo.
        """
        return ContractGetInfoResponse.ContractInfo(
            accountID=self.account_id._to_proto() if self.account_id else None,
            contractID=self.contract_id._to_proto() if self.contract_id else None,
            contractAccountID=self.contract_account_id,
            adminKey=self.admin_key._to_proto() if self.admin_key else None,
            expirationTime=(
                self.expiration_time._to_protobuf() if self.expiration_time else None
            ),
            autoRenewPeriod=(
                self.auto_renew_period._to_proto() if self.auto_renew_period else None
            ),
            storage=self.storage,
            memo=self.contract_memo,
            balance=self.balance,
            deleted=self.is_deleted,
            tokenRelationships=[
                relationship._to_proto() for relationship in self.token_relationships
            ],
            ledger_id=self.ledger_id,
            auto_renew_account_id=(
                self.auto_renew_account_id._to_proto()
                if self.auto_renew_account_id
                else None
            ),
            max_automatic_token_associations=self.max_automatic_token_associations,
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the ContractInfo object.

        Returns:
            str: A string representation of the ContractInfo object.
        """
        return self.__str__()

    def __str__(self) -> str:
        """
        Pretty-print the ContractInfo.
        """
        # Format expiration time as datetime if available
        exp_dt = (
            datetime.datetime.fromtimestamp(self.expiration_time.seconds)
            if self.expiration_time and hasattr(self.expiration_time, "seconds")
            else self.expiration_time
        )

        # Format keys as readable strings
        token_relationships_str = (
            [str(relationship) for relationship in self.token_relationships]
            if self.token_relationships
            else []
        )

        # Format ledger_id as hex if it's bytes
        ledger_id_display = (
            f"0x{self.ledger_id.hex()}"
            if isinstance(self.ledger_id, (bytes, bytearray))
            else self.ledger_id
        )

        return (
            "ContractInfo(\n"
            f"  contract_id={self.contract_id},\n"
            f"  account_id={self.account_id},\n"
            f"  contract_account_id={self.contract_account_id},\n"
            f"  admin_key={self.admin_key},\n"
            f"  auto_renew_account_id={self.auto_renew_account_id},\n"
            f"  auto_renew_period={self.auto_renew_period},\n"
            f"  storage={self.storage},\n"
            f"  contract_memo='{self.contract_memo}',\n"
            f"  balance={self.balance},\n"
            f"  expiration_time={exp_dt},\n"
            f"  is_deleted={self.is_deleted},\n"
            f"  token_relationships={token_relationships_str},\n"
            f"  ledger_id={ledger_id_display},\n"
            f"  max_automatic_token_associations={self.max_automatic_token_associations}\n"
            ")"
        )

    @classmethod
    def _from_proto_field(
        cls,
        proto: ContractGetInfoResponse.ContractInfo,
        field_name: str,
        from_proto: Callable,
    ):
        """
        Helper to extract and convert proto fields to a python object.

        Args:
            proto: The protobuf object to extract the field from.
            field_name: The name of the field to extract.
            from_proto: A callable to convert the field from protobuf to a python object.

        Returns:
            The converted field value or None if the field doesn't exist.
        """
        if not proto.HasField(field_name):
            return None

        value = getattr(proto, field_name)
        return from_proto(value)
