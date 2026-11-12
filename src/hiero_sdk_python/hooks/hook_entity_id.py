"""HookEntityId class for HIP-1195 hooks."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import basic_types_pb2


@dataclass(frozen=True)
class HookEntityId:
    """
    The ID of an entity that owns a hook: either an account or a contract.

    Exactly one of `account_id` or `contract_id` must be set.

    Attributes:
        account_id (AccountId, optional): The account that owns the hook.
        contract_id (ContractId, optional): The contract that owns the hook.
    """

    account_id: AccountId | None = None
    contract_id: ContractId | None = None

    def __post_init__(self) -> None:
        """
        Validates that exactly one entity ID of the correct type is set.

        Raises:
            ValueError: If neither or both IDs are set.
            TypeError: If an ID has the wrong type.
        """
        if (self.account_id is None) == (self.contract_id is None):
            raise ValueError("HookEntityId requires exactly one of account_id or contract_id.")
        if self.account_id is not None and not isinstance(self.account_id, AccountId):
            raise TypeError("account_id must be an AccountId instance.")
        if self.contract_id is not None and not isinstance(self.contract_id, ContractId):
            raise TypeError("contract_id must be a ContractId instance.")

    @property
    def is_account(self) -> bool:
        """Returns True if the hook is owned by an account."""
        return self.account_id is not None

    @property
    def is_contract(self) -> bool:
        """Returns True if the hook is owned by a contract."""
        return self.contract_id is not None

    def _to_proto(self) -> basic_types_pb2.HookEntityId:
        """Converts this HookEntityId to its protobuf representation."""
        if self.account_id is not None:
            return basic_types_pb2.HookEntityId(account_id=self.account_id._to_proto())
        return basic_types_pb2.HookEntityId(contract_id=self.contract_id._to_proto())

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.HookEntityId) -> HookEntityId:
        """
        Creates a HookEntityId from its protobuf representation.

        Raises:
            ValueError: If the protobuf has neither an account nor a contract ID set.
        """
        entity = proto.WhichOneof("entity_id")
        if entity == "account_id":
            return cls(account_id=AccountId._from_proto(proto.account_id))
        if entity == "contract_id":
            return cls(contract_id=ContractId._from_proto(proto.contract_id))
        raise ValueError("HookEntityId proto must have either account_id or contract_id set.")
