"""EvmHookSpec and EvmHook classes for HIP-1195 hooks."""

from __future__ import annotations

from dataclasses import dataclass, field

from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import hook_types_pb2
from hiero_sdk_python.hooks.evm_hook_storage_update import EvmHookStorageUpdate


@dataclass
class EvmHookSpec:
    """
    The source of an EVM hook's bytecode.

    Hooks are currently implemented by an existing contract that implements the
    extension point's interface.

    Attributes:
        contract_id (ContractId, optional): The contract that implements the hook.
    """

    contract_id: ContractId | None = None

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If contract_id is not a ContractId.
        """
        if self.contract_id is not None and not isinstance(self.contract_id, ContractId):
            raise TypeError("contract_id must be a ContractId instance.")

    def _to_spec_proto(self) -> hook_types_pb2.EvmHookSpec:
        """
        Converts this spec to its protobuf representation.

        Raises:
            ValueError: If contract_id is not set.
        """
        if self.contract_id is None:
            raise ValueError("EVM hook requires a contract_id.")
        return hook_types_pb2.EvmHookSpec(contract_id=self.contract_id._to_proto())


@dataclass
class EvmHook(EvmHookSpec):
    """
    An EVM hook: the contract implementing it plus its initial storage.

    Attributes:
        contract_id (ContractId, optional): The contract that implements the hook.
        storage_updates (list[EvmHookStorageUpdate]): Storage written when the
            hook is created.
    """

    storage_updates: list[EvmHookStorageUpdate] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If a field has the wrong type.
        """
        super().__post_init__()
        self.storage_updates = list(self.storage_updates)
        if not all(isinstance(update, EvmHookStorageUpdate) for update in self.storage_updates):
            raise TypeError("storage_updates must be EvmHookStorageUpdate instances.")

    def _to_proto(self) -> hook_types_pb2.EvmHook:
        """
        Converts this hook to its protobuf representation.

        Raises:
            ValueError: If contract_id is not set.
        """
        return hook_types_pb2.EvmHook(
            spec=self._to_spec_proto(),
            storage_updates=[update._to_proto() for update in self.storage_updates],
        )

    @classmethod
    def _from_proto(cls, proto: hook_types_pb2.EvmHook) -> EvmHook:
        """Creates an EvmHook from its protobuf representation."""
        contract_id = None
        if proto.HasField("spec") and proto.spec.HasField("contract_id"):
            contract_id = ContractId._from_proto(proto.spec.contract_id)
        return cls(
            contract_id=contract_id,
            storage_updates=[EvmHookStorageUpdate._from_proto(update) for update in proto.storage_updates],
        )
