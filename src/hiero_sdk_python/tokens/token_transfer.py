"""
hiero_sdk_python.tokens.token_transfer.py.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenTransfer for representing Token transfer details.
"""

from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.hooks.fungible_hook_call import FungibleHookCall
from hiero_sdk_python.tokens.token_id import TokenId


class TokenTransfer:
    """
    Represents a single fungible token transfer, detailing the token, the account involved,
    the amount, and optional approval status and decimal expectations.
    """

    def __init__(
        self,
        token_id: TokenId,
        account_id: AccountId,
        amount: int,
        expected_decimals: int | None = None,
        is_approved: bool = False,
        hook_call: FungibleHookCall | None = None,
    ) -> None:
        """
        Initializes a new TokenTransfer instance.

        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of the token to send or receive.
            expected_decimals (int, optional):
                The number specifying the amount in the smallest denomination.
            is_approved (bool, optional): Indicates whether this transfer is an approved allowance.
            hook_call (FungibleHookCall, optional): An account allowance hook to call
                for this transfer (HIP-1195).
        """
        self.token_id: TokenId = token_id
        self.account_id: AccountId = account_id
        self.amount: int = amount
        self.expected_decimals: int | None = expected_decimals
        self.is_approved: bool = is_approved
        self.hook_call: FungibleHookCall | None = hook_call

    def _to_proto(self) -> basic_types_pb2.AccountAmount:
        """
        Converts this TokenTransfer instance to its protobuf representation, AccountAmount.

        Returns:
            AccountAmount: The protobuf representation of this TokenTransfer.

        Raises:
            ValueError: If both is_approved and hook_call are set.
        """
        proto = basic_types_pb2.AccountAmount(
            accountID=self.account_id._to_proto(), amount=self.amount, is_approval=self.is_approved
        )
        if self.hook_call is not None:
            if self.is_approved:
                raise ValueError("An approved transfer cannot also call an allowance hook.")
            self.hook_call._apply_to(proto)
        return proto

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.TokenTransferList) -> list[TokenTransfer]:
        """
        Construct a list of TokenTransfer from the protobuf of TokenTransferList.

        Args:
        proto (basic_types_pb2.TokenTransferList:
            The protobuf representation of a TokenTransferList
        """
        expected_decimals = proto.expected_decimals.value if proto.HasField("expected_decimals") else None

        return [
            TokenTransfer(
                token_id=TokenId._from_proto(proto.token),
                account_id=AccountId._from_proto(transfer.accountID),
                amount=transfer.amount,
                expected_decimals=expected_decimals,
                is_approved=transfer.is_approval,
                hook_call=FungibleHookCall._from_account_amount(transfer),
            )
            for transfer in proto.transfers
        ]

    def __str__(self) -> str:
        """
        Returns a string representation of this TokenTransfer instance.

        Returns:
            str: A string representation of this TokenTransfer.
        """
        return (
            f"TokenTransfer("
            f"token_id={self.token_id}, "
            f"account_id={self.account_id}, "
            f"amount={self.amount}, "
            f"expected_decimals={self.expected_decimals}, "
            f"is_approved={self.is_approved}"
            f"{f', hook_call={self.hook_call}' if self.hook_call is not None else ''})"
        )
