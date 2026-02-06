"""
Represents a Contract ID on the Hedera network.

Provides utilities for creating, parsing from strings, converting to protobuf
format, and validating checksums associated with a contract.
"""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.entity_id_helper import (
    parse_from_string,
    validate_checksum,
    format_to_string_with_checksum,
    to_solidity_address,
    perform_query_to_mirror_node,
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
        if contract_id_proto.HasField("evm_address"):
            return cls(
                shard=contract_id_proto.shardNum,
                realm=contract_id_proto.realmNum,
                evm_address=contract_id_proto.evm_address,
            )

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
            TypeError: If input is not a string.
            ValueError: If the contract ID string is None, not a string,
                or in an invalid format.
        """
        if contract_id_str is None or not isinstance(contract_id_str, str):
            raise TypeError(
                f"contract_id_str must be of type str, got {type(contract_id_str).__name__}"
            )

        evm_address_match = EVM_ADDRESS_REGEX.match(contract_id_str)

        if evm_address_match:
            shard, realm, evm_address = evm_address_match.groups()
            return cls(
                shard=int(shard),
                realm=int(realm),
                evm_address=bytes.fromhex(evm_address),
            )

        else:
            try:
                shard, realm, contract, checksum = parse_from_string(contract_id_str)

                contract_id: ContractId = cls(
                    shard=int(shard), realm=int(realm), contract=int(contract)
                )
                object.__setattr__(contract_id, "checksum", checksum)
                return contract_id

            except Exception as e:
                raise ValueError(
                    f"Invalid contract ID string '{contract_id_str}'. "
                    f"Expected format 'shard.realm.contract'."
                ) from e

    @classmethod
    def from_evm_address(cls, shard: int, realm: int, evm_address: str) -> "ContractId":
        """
        Create a ContractId from an EVM address string.

        Args:
            shard (int): Shard number.
            realm (int): Realm number.
            evm_address (str): Hex-encoded EVM address.

        Returns:
            ContractId: A new ContractId instance.

        Raises:
            TypeError: If any argument is of incorrect type.
            ValueError: If shard or realm are negative, or the EVM address is invalid.
        """
        if not isinstance(evm_address, str):
            raise TypeError(
                f"evm_address must be of type str, got {type(evm_address).__name__}"
            )

        for name, value in (("shard", shard), ("realm", realm)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be int, got {type(value).__name__}")
            if value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

        try:
            # throw error internally if not valid evm_address
            evm_addr = EvmAddress.from_string(evm_address=evm_address)
            return cls(shard=shard, realm=realm, evm_address=evm_addr.address_bytes)
        except Exception as e:
            raise ValueError(f"Invalid EVM address: {evm_address}") from e

    @classmethod
    def from_bytes(cls, data: bytes) -> "ContractId":
        """
        Deserialize an ContractId from protobuf-encoded bytes.

        Args:
            data (bytes): Protobuf-encoded `ContractID` message.

        Returns:
            ContractId: Reconstructed ContractId instance.

        Raises:
            TypeError: If data is not bytes.
            ValueError: If deserialization fails.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")

        try:
            proto = basic_types_pb2.ContractID.FromString(data)
        except Exception as exc:
            raise ValueError("Failed to deserialize ContractId from bytes") from exc

        return cls._from_proto(proto)

    def to_bytes(self) -> "bytes":
        """
        Serialize this ContractId to protobuf bytes.

        Returns:
            bytes: Protobuf-encoded representation of this ContractId.
        """
        return self._to_proto().SerializeToString()

    def populate_contract_num(self, client: "Client") -> "ContractId":
        """
        Resolve and populate the numeric contract ID using the Mirror Node.

        This method requires the ContractId to contain an EVM address.

        Args:
            client (Client): Client configured with a mirror network.

        Returns:
            ContractId: New instance with the resolved contract number.

        Raises:
            ValueError: If no EVM address is present or the response is invalid.
            RuntimeError: If the mirror node request fails.
        """
        if self.evm_address is None:
            raise ValueError("evm_address is required to populate the contract number")

        url = f"{client.network.get_mirror_rest_url()}/contracts/{self.evm_address.hex()}"

        try:
            response = perform_query_to_mirror_node(url)
            contract_id = response.get("contract_id")
            if not contract_id:
                raise ValueError("Mirror node response missing 'contract_id'")

        except RuntimeError as e:
            raise RuntimeError(
                "Failed to populate contract num from mirror node for evm_address "
                f"{self.evm_address.hex()}"
            ) from e

        try:
            contract = int(contract_id.split(".")[-1])
            return ContractId(
                shard=self.shard,
                realm=self.realm,
                contract=contract,
                evm_address=self.evm_address,
            )
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid contract_id format received: {contract_id}") from e

    def __str__(self) -> str:
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

    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the ContractId for debugging.

        Returns:
            str: ContractId(shard=X, realm=Y, contract=Z) or
            ContractId(shard=X, realm=Y, evm_address=...) if evm_address is set.
        """
        if self.evm_address is not None:
            return f"ContractId(shard={self.shard}, realm={self.realm}, evm_address={self.evm_address.hex()})"

        return f"ContractId(shard={self.shard}, realm={self.realm}, contract={self.contract})"

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

        return to_solidity_address(self.shard, self.realm, self.contract)

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
            raise ValueError(
                "to_string_with_checksum cannot be applied to ContractId with evm_address"
            )

        return format_to_string_with_checksum(
            self.shard, self.realm, self.contract, client
        )

