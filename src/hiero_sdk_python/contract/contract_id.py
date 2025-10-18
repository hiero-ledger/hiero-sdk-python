"""
Contract ID class.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.entity_id_helper import (
    parse_from_string,
    validate_checksum,
    format_to_string_with_checksum
)


@dataclass(frozen=True)
class ContractId:
    """
    Represents a contract ID on the network.

    A contract ID consists of three components: shard, realm, and contract (number).
    These components uniquely identify a contract in the network.

    Attributes:
        shard (int): The shard number. Defaults to 0.
        realm (int): The realm number. Defaults to 0.
        contract (int): The contract number. Defaults to 0.
        evm_address (bytes): The EVM address of the contract. Defaults to None.
    """

    shard: int = 0
    realm: int = 0
    contract: int = 0
    evm_address: Optional[bytes] = None
    checksum: str | None = field(default=None, init=False)

    @classmethod
    def _from_proto(cls, contract_id_proto: basic_types_pb2.ContractID) -> "ContractId":
        """
        Creates a ContractId instance from a protobuf ContractID object.
        """
        return cls(
            shard=contract_id_proto.shardNum,
            realm=contract_id_proto.realmNum,
            contract=contract_id_proto.contractNum,
        )

    def _to_proto(self):
        """
        Converts the ContractId instance to a protobuf ContractID object.
        """
        return basic_types_pb2.ContractID(
            shardNum=self.shard,
            realmNum=self.realm,
            contractNum=self.contract,
            evm_address=self.evm_address,
        )

    @classmethod
    def from_string(cls, contract_id_str: str) -> "ContractId":
        """
        Parses a string in the format 'shard.realm.contract' to create a ContractId instance.
        """
        try:
            shard, realm, contract, checksum = parse_from_string(contract_id_str)
            
            contract_id: ContractId =  cls(
                shard=int(shard),
                realm=int(realm),
                contract=int(contract)
            )
            object.__setattr__(contract_id, "checksum", checksum)

            return contract_id
        except Exception as e:
            raise ValueError(
                f"Invalid contract ID string '{contract_id_str}'. Expected format 'shard.realm.contract'."
            ) from e

    def __str__(self):
        """
        Returns the string representation of the ContractId in the format 'shard.realm.contract'.
        """
        return f"{self.shard}.{self.realm}.{self.contract}"

    def to_evm_address(self) -> str:
        """
        Converts the ContractId to an EVM address.
        """
        if self.evm_address is not None:
            return self.evm_address.hex()

        # If evm_address is not set, compute the EVM address from shard, realm, and contract.
        # The EVM address is a 20-byte value:
        # [4 bytes shard][8 bytes realm][8 bytes contract], all big-endian.
        shard_bytes = (0).to_bytes(4, "big")
        realm_bytes = (0).to_bytes(8, "big")
        contract_bytes = self.contract.to_bytes(8, "big")
        evm_bytes = shard_bytes + realm_bytes + contract_bytes

        return evm_bytes.hex()

    def validate_checksum(self, client: "Client") -> None:
        """Validate the checksum for the contractId"""
        validate_checksum(
            self.shard,
            self.realm,
            self.contract,
            self.checksum,
            client,
        )
    
    def to_string_with_checksum(self, client: "Client") -> str:
        """
        Returns the string representation of the ContractId with checksum 
        in 'shard.realm.contract-checksum' format.
        """
        return format_to_string_with_checksum(
            self.shard, 
            self.realm, 
            self.contract, 
            client
        )
