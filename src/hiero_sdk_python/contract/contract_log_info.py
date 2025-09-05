"""
This module contains the ContractLogInfo class, which represents a log entry
from a contract execution.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import contract_types_pb2


@dataclass
class ContractLogInfo:
    """
    Represents a log entry from a contract execution.

    Attributes:
        contract_id (Optional[ContractId]): The contract ID.
        bloom (Optional[bytes]): The bloom filter.
        topics (List[bytes]): The topics.
        data (Optional[bytes]): The data.
    """

    contract_id: Optional[ContractId] = None
    bloom: Optional[bytes] = None
    topics: List[bytes] = field(default_factory=list)
    data: Optional[bytes] = None

    @classmethod
    def _from_proto(
        cls, proto: contract_types_pb2.ContractLoginfo
    ) -> "ContractLogInfo":
        """
        Creates a ContractLogInfo instance from its protobuf representation.

        Args:
            proto (contract_types_pb2.ContractLoginfo): The protobuf object to convert.

        Returns:
            ContractLogInfo: The corresponding ContractLogInfo instance.

        Raises:
            ValueError: If the protobuf object is None.
        """
        if proto is None:
            raise ValueError("Contract log info proto is None")

        return cls(
            contract_id=(
                ContractId._from_proto(proto.contractID) if proto.contractID else None
            ),
            bloom=proto.bloom,
            topics=proto.topic,
            data=proto.data,
        )

    def _to_proto(self) -> contract_types_pb2.ContractLoginfo:
        """
        Converts this ContractLogInfo instance to its protobuf representation.

        Returns:
            contract_types_pb2.ContractLoginfo: The protobuf object representing this instance.
        """
        return contract_types_pb2.ContractLoginfo(
            contractID=self.contract_id._to_proto() if self.contract_id else None,
            bloom=self.bloom,
            topic=self.topics,
            data=self.data,
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the ContractLogInfo object.

        Returns:
            str: A string representation of the ContractLogInfo object.
        """
        return self.__str__()

    def __str__(self) -> str:
        """
        Pretty-print the ContractLogInfo.
        """
        topics_str = [topic.hex() for topic in self.topics] if self.topics else []

        return (
            "ContractLogInfo("
            f"contract_id={self.contract_id}, "
            f"bloom={self.bloom.hex() if self.bloom else None}, "
            f"topics={topics_str}, "
            f"data={self.data.hex() if self.data else None}"
            ")"
        )
