from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.entity_id_helper import format_to_string_with_checksum

if TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client


@dataclass(frozen=True)
class DelegateContractId(ContractId):
    """
    Represents a delegatable contract identifier used as a key in the Hiero network.

    A DelegateContractId is a permissive key type that designates a smart contract
    authorized to sign a transaction if it is the recipient of the active message
    frame. Unlike a standard ContractID, this key type does not require the code
    executing in the current frame to belong to the specified contract.
    """

    def to_proto_key(self) -> basic_types_pb2.Key:
        return basic_types_pb2.Key(delegatable_contract_id=self._to_proto())

    def __str__(self) -> str:
        """
        Returns the string representation of the DelegateContractId.

        Format will be 'shard.realm.contract' or 'shard.realm.evm_address_hex'
        if evm_address is set. Does not include a checksum.

        Returns:
          str: The string representation of the ContractId.
        """
        if self.evm_address is not None:
            return f"{self.shard}.{self.realm}.{self.evm_address.hex()}"

        return f"{self.shard}.{self.realm}.{self.contract}"

    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the ContractId for debugging.

        Returns:
          str: DelegateContractId(shard=X, realm=Y, contract=Z) or
          DelegateContractId(shard=X, realm=Y, evm_address=...) if evm_address is set.
        """
        if self.evm_address is not None:
            return f"DelegateContractId(shard={self.shard}, realm={self.realm}, evm_address={self.evm_address.hex()})"

        return f"DelegateContractId(shard={self.shard}, realm={self.realm}, contract={self.contract})"

    def to_string_with_checksum(self, client: Client) -> str:
        """
        Generates a string representation with a network-specific checksum.

        Format: 'shard.realm.contract-checksum' (e.g., "0.0.123-vfmkw").

        Args:
          client (Client): The client instance used to generate the
            network-specific checksum.

        Returns:
          str: The string representation with checksum.

        Raises:
          ValueError: If the DelegateContractId has an `evm_address` set,
                    as checksums cannot be applied to EVM addresses.
        """
        if self.evm_address is not None:
            raise ValueError("to_string_with_checksum cannot be applied to DelegateContractId with evm_address")

        return format_to_string_with_checksum(self.shard, self.realm, self.contract, client)
