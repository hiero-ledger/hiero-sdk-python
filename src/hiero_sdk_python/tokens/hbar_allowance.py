"""
HbarAllowance class for handling HBAR allowances.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2 import (
    CryptoAllowance as CryptoAllowanceProto,
)


@dataclass
class HbarAllowance:
    """
    Represents a HBAR allowance for the network.

    This class encapsulates HBAR allowance information including the owner account,
    spender account, and amount.

    Attributes:
        owner_account_id (Optional[AccountId]): The account that owns the HBAR.
        spender_account_id (Optional[AccountId]): The account permitted to transfer the HBAR.
        amount (int): The amount of HBAR allowed for transfer (in tinybars).
    """

    owner_account_id: Optional[AccountId] = None
    spender_account_id: Optional[AccountId] = None
    amount: int = 0

    @classmethod
    def _from_proto(cls, proto: CryptoAllowanceProto) -> "HbarAllowance":
        """
        Creates a HbarAllowance instance from its protobuf representation.

        Args:
            proto (CryptoAllowanceProto): The protobuf HbarAllowance object to convert.

        Returns:
            HbarAllowance: A new HbarAllowance instance.

        Raises:
            ValueError: If the proto is None.
        """
        if proto is None:
            raise ValueError("HbarAllowance proto is None")

        return cls(
            owner_account_id=(cls._from_proto_field(proto, "owner", AccountId._from_proto)),
            spender_account_id=(cls._from_proto_field(proto, "spender", AccountId._from_proto)),
            amount=proto.amount,
        )

    def _to_proto(self) -> CryptoAllowanceProto:
        """
        Converts this HbarAllowance instance to its protobuf representation.

        Returns:
            CryptoAllowanceProto: The protobuf representation of this HbarAllowance.
        """
        proto = CryptoAllowanceProto()

        if self.owner_account_id is not None:
            proto.owner.CopyFrom(self.owner_account_id._to_proto())

        if self.spender_account_id is not None:
            proto.spender.CopyFrom(self.spender_account_id._to_proto())

        proto.amount = self.amount

        return proto

    def __str__(self) -> str:
        """
        Returns a string representation of the HbarAllowance object.

        Returns:
            str: A string representation of the HbarAllowance object.
        """
        if self.owner_account_id is not None and self.spender_account_id is not None:
            return (
                f"HbarAllowance("
                f"owner_account_id={self.owner_account_id}, "
                f"spender_account_id={self.spender_account_id}, "
                f"amount={self.amount}"
                f")"
            )
        elif self.owner_account_id is not None:
            return (
                f"HbarAllowance("
                f"owner_account_id={self.owner_account_id}, "
                f"amount={self.amount}"
                f")"
            )
        elif self.spender_account_id is not None:
            return (
                f"HbarAllowance("
                f"spender_account_id={self.spender_account_id}, "
                f"amount={self.amount}"
                f")"
            )
        else:
            return f"HbarAllowance(amount={self.amount})"

    def __repr__(self) -> str:
        """
        Returns a string representation of the HbarAllowance object.

        Returns:
            str: A string representation of the HbarAllowance object.
        """
        return self.__str__()

    @classmethod
    def _from_proto_field(
        cls,
        proto: Any,
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
