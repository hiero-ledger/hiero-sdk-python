"""
This module defines the ContractNonceInfo dataclass, which represents the nonce information
associated with a specific smart contract on the network. The nonce is an integer value
that is incremented with each transaction or contract creation, and is used to prevent replay
attacks and ensure transaction uniqueness.
"""

from dataclasses import dataclass
from typing import Optional

from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import contract_types_pb2


@dataclass
class ContractNonceInfo:
    """
    Represents the nonce information for a specific contract.

    Attributes:
        contract_id (Optional[ContractId]): The contract identifier.
        nonce (int): The nonce value associated with the contract.
    """

    contract_id: Optional[ContractId] = None
    nonce: int = 0

    @classmethod
    def _from_proto(
        cls, proto: contract_types_pb2.ContractNonceInfo
    ) -> "ContractNonceInfo":
        """
        Creates a ContractNonceInfo instance from its protobuf representation.

        Args:
            proto (contract_types_pb2.ContractNonceInfo): The protobuf object to convert.

        Returns:
            ContractNonceInfo: The corresponding ContractNonceInfo instance.

        Raises:
            ValueError: If the protobuf object is None.
        """
        if proto is None:
            raise ValueError("Contract nonce info proto is None")

        return cls(
            contract_id=ContractId._from_proto(proto.contract_id), nonce=proto.nonce
        )

    def _to_proto(self) -> contract_types_pb2.ContractNonceInfo:
        """
        Converts this ContractNonceInfo instance to its protobuf representation.

        Returns:
            contract_types_pb2.ContractNonceInfo: The protobuf object representing this instance.
        """
        return contract_types_pb2.ContractNonceInfo(
            contract_id=self.contract_id._to_proto(), nonce=self.nonce
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the ContractNonceInfo object.

        Returns:
            str: A string representation of the ContractNonceInfo object.
        """
        return self.__str__()

    def __str__(self) -> str:
        """
        Pretty-print the ContractNonceInfo.
        """
        return (
            "ContractNonceInfo("
            f"contract_id={self.contract_id}, "
            f"nonce={self.nonce}"
            ")"
        )
