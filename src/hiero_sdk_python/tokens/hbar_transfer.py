"""
Defines HbarTransfer for representing and converting HBAR transfer details
(account, amount, approval) to and from protobuf messages.
"""

from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2


class HbarTransfer:
    """
    Represents a transfer of HBAR to or from an account.

    This class encapsulates the details of an HBAR transfer, including the account,
    amount, and whether the transfer is approved.
    """

    def __init__(
        self,
        account_id: Optional[AccountId] = None,
        amount: Optional[int] = None,
        is_approved: bool = False,
    ) -> None:
        """
        Initializes a new HbarTransfer instance.

        Args:
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of HBAR to transfer (in tinybars).
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.
        """
        self.account_id: Optional[AccountId] = account_id
        self.amount: Optional[int] = amount
        self.is_approved: bool = is_approved

    def _to_proto(self) -> basic_types_pb2.AccountAmount:
        """
        Converts this HbarTransfer instance to its protobuf representation.

        Returns:
            basic_types_pb2.AccountAmount: The protobuf representation of this HBAR transfer.
        """
        return basic_types_pb2.AccountAmount(
            accountID=self.account_id._to_proto() if self.account_id else None,
            amount=self.amount,
            is_approval=self.is_approved,
        )

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.AccountAmount) -> "HbarTransfer":
        """
        Creates a HbarTransfer from a protobuf representation.

        Args:
            proto (basic_types_pb2.AccountAmount): The protobuf AccountAmount object.

        Returns:
            HbarTransfer: A new HbarTransfer instance.
        """
        if proto is None:
            raise ValueError("HbarTransfer proto is None")

        return cls(
            account_id=(AccountId._from_proto(proto.accountID)),
            amount=proto.amount,
            is_approved=proto.is_approval,
        )

    def __str__(self) -> str:
        """
        Returns a string representation of this HbarTransfer instance.

        Returns:
            str: A string representation of this HBAR transfer.
        """
        return (
            "HbarTransfer("
            f"account_id={self.account_id}, "
            f"amount={self.amount}, "
            f"is_approved={self.is_approved}"
            ")"
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of this HbarTransfer instance.

        Returns:
            str: A string representation of this HBAR transfer.
        """
        return self.__str__()
