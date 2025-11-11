"""
Represents a Contract ID on the Hedera network.

Provides utilities for creating, parsing from strings, converting to protobuf
format, and validating checksums associated with a contract.
"""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.entity_id_helper import (
    parse_from_string,
    validate_checksum,
    format_to_string_with_checksum
)

if TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client

EVM_ADDRESS_REGEX = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.([a-fA-F0-9]{40}$)")


@dataclass(frozen=True)
class ContractId:
    """
    Represents a unique contract ID on the Hedera network.

    A contract ID can be represented by its shard, realm, and contract number,
    or by a 20-byte EVM address.

    Attributes:
        shard (int): The shard number (non-negative). Defaults to 0.
        realm (int): The realm number (non-negative). Defaults to 0.
        contract (int): The contract number (non-negative). Defaults to 0.
        evm_address (Optional[bytes]): The 20-byte EVM address of the contract.
            Defaults to None.
        checksum (Optional[str]): A network-specific checksum computed from
            the shard, realm, and contract numbers. Not used if `evm_address`
            is set.
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

        Args:
            contract_id_proto (basic_types_pb2.ContractID): The protobuf
                ContractID object to convert from.

        Returns:
            ContractId: A new ContractId instance populated with data from
            the protobuf object.
        """
        return cls(
            shard=contract_id_proto.shardNum,
            realm=contract_id_proto.realmNum,
            contract=contract_id_proto.contractNum,
        )

    def _to_proto(self):
        """
        Converts the ContractId instance to a protobuf ContractID object.

        Returns:
            basic_types_pb2.ContractID: The corresponding protobuf
            ContractID object.
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
        Parses a string to create a ContractId instance.

        The string can be in the format 'shard.realm.contract' (e.g., "0.0.123"),
        'shard.realm.contract-checksum' (e.g., "0.0.123-vfmkw"),
        or 'shard.realm.evm_address' (e.g., "0.0.a...f").

        Args:
            contract_id_str (str): The contract ID string to parse.

        Returns:
            ContractId: A new ContractId instance.

        Raises:
            ValueError: If the contract ID string is None, not a string,
                or in an invalid format.
        """
        if contract_id_str is None or not isinstance(contract_id_str, str):
            raise ValueError(
                f"Invalid contract ID string '{contract_id_str}'. "
                f"Expected format 'shard.realm.contract'."
            )

        evm_address_match = EVM_ADDRESS_REGEX.match(contract_id_str)

        if evm_address_match:
            shard, realm, evm_address = evm_address_match.groups()
            return cls(
                shard=int(shard),
                realm=int(realm),
                evm_address=bytes.fromhex(evm_address)
            )

        else:
            try:
                shard, realm, contract, checksum = parse_from_string(contract_id_str)

                contract_id: ContractId = cls(
                    shard=int(shard),
                    realm=int(realm),
                    contract=int(contract)
                )
                object.__setattr__(contract_id, "checksum", checksum)
                return contract_id

            except Exception as e:
                raise ValueError(
                    f"Invalid contract ID string '{contract_id_str}'. "
                    f"Expected format 'shard.realm.contract'."
                ) from e

    def __str__(self):
        """
        Returns the string representation of the ContractId.

        Format will be 'shard.realm.contract' or 'shard.realm.evm_address_hex'
        if evm_address is set. Does not include a checksum.

        Returns:
            str: The string representation of the ContractId.
        """
        if self.evm_address is not None:
            return f"{self.shard}.{self.realm}.{self.evm_address.hex()}"

        return f"{self.shard}.{self.realm}.{self.contract}"

    def to_evm_address(self) -> str:
        """
        Converts the ContractId to a 20-byte EVM address string (hex).

        If the `evm_address` attribute is set, it returns that.
        Otherwise, it computes the 20-byte EVM address from the shard, realm,
        and contract numbers (e.g., [4-byte shard][8-byte realm][8-byte contract]).

        Returns:
            str: The 20-byte EVM address as a hex-encoded string.
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
        """
        Validates the checksum (if present) against a client's network.

        The checksum is validated against the ledger ID of the provided client.
        This method does nothing if no checksum is present on the ContractId.

        Args:
            client (Client): The client instance, which contains the network
                ledger ID used for checksum validation.

        Raises:
            ValueError: If the checksum is present but invalid or does not
                match the client's network.
        """
        validate_checksum(
            self.shard,
            self.realm,
            self.contract,
            self.checksum,
            client,
        )

    def to_string_with_checksum(self, client: "Client") -> str:
        """
        Generates a string representation with a network-specific checksum.

        Format: 'shard.realm.contract-checksum' (e.g., "0.0.123-vfmkw").

        Args:
            client (Client): The client instance used to generate the
                network-specific checksum.

        Returns:
            str: The string representation with checksum.

        Raises:
            ValueError: If the ContractId has an `evm_address` set,
                as checksums cannot be applied to EVM addresses.
        """
        if self.evm_address is not None:
            raise ValueError("to_string_with_checksum cannot be applied to ContractId with evm_address")

        return format_to_string_with_checksum(
            self.shard,
            self.realm,
            self.contract,
            client
        )