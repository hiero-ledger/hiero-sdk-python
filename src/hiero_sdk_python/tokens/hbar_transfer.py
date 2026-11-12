"""
Defines HbarTransfer for representing and converting HBAR transfer details
(account, amount, approval) to and from protobuf messages.
"""

from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.hooks.fungible_hook_call import FungibleHookCall


class HbarTransfer:
    """
    Represents a transfer of HBAR to or from an account.

    This class encapsulates the details of an HBAR transfer, including the account,
    amount, and whether the transfer is approved.
    """

    def __init__(
        self,
        account_id: AccountId | None = None,
        amount: int | None = None,
        is_approved: bool = False,
        hook_call: FungibleHookCall | None = None,
    ) -> None:
        """
        Initializes a new HbarTransfer instance.

        Args:
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of HBAR to transfer (in tinybars).
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.
            hook_call (FungibleHookCall, optional): An account allowance hook to call
                for this transfer (HIP-1195).
        """
        self.account_id: AccountId | None = account_id
        self.amount: int | None = amount
        self.is_approved: bool = is_approved
        self.hook_call: FungibleHookCall | None = hook_call

    def _to_proto(self) -> basic_types_pb2.AccountAmount:
        """
        Converts this HbarTransfer instance to its protobuf representation.

        Returns:
            basic_types_pb2.AccountAmount: The protobuf representation of this HBAR transfer.

        Raises:
            ValueError: If both is_approved and hook_call are set.
        """
        proto = basic_types_pb2.AccountAmount(
            accountID=self.account_id._to_proto() if self.account_id else None,
            amount=self.amount,
            is_approval=self.is_approved,
        )
        if self.hook_call is not None:
            if self.is_approved:
                raise ValueError("An approved transfer cannot also call an allowance hook.")
            self.hook_call._apply_to(proto)
        return proto

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.AccountAmount) -> HbarTransfer:
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
            hook_call=FungibleHookCall._from_account_amount(proto),
        )

    def __str__(self) -> str:
        """
        Returns a string representation of this HbarTransfer instance.

        Returns:
            str: A string representation of this HBAR transfer.
        """
        hook = f", hook_call={self.hook_call}" if self.hook_call is not None else ""
        return f"HbarTransfer(account_id={self.account_id}, amount={self.amount}, is_approved={self.is_approved}{hook})"

    def __repr__(self) -> str:
        """
        Returns a string representation of this HbarTransfer instance.

        Returns:
            str: A string representation of this HBAR transfer.
        """
        return self.__str__()
